"""Модели CRM автосервиса.

Схема связей:

    Client ←(1:N)— Car ←(1:N)— WorkOrder

  - у клиента может быть несколько машин (он и жена ездят),
  - у машины может быть несколько заказ-нарядов за всю историю.

Клиент из заказ-наряда достаётся через `order.car.client`.
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.fields import PhoneField
from core.validators import validate_license_plate, validate_vin
from core.constants import PAYMENT_METHODS, SERVICES

# Формируем список вариантов для поля service
SERVICE_CHOICES = [(code, data["name"]) for code, data in SERVICES.items()]


class Client(models.Model):
    """Клиент автосервиса.

    Ключ поиска — телефон. Один клиент = один нормализованный номер.
    Если человек с тем же телефоном уже есть — Django не даст создать
    дубль (unique=True), и это правильно.
    """

    name = models.CharField("ФИО", max_length=100)
    phone = PhoneField("Телефон", unique=True)
    notes = models.TextField(
        "Заметки",
        blank=True,
        help_text="Видно только в CRM. Например, «постоянный клиент», «платит картой».",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class Master(models.Model):
    """Мастер (сотрудник), выполняющий работы."""

    name = models.CharField("ФИО", max_length=150)
    is_active = models.BooleanField(
        "Работает", default=True,
        help_text="Снимите галочку, если мастер уволился (скроется из выбора)."
    )
    notes = models.TextField("Заметки", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Car(models.Model):
    """Автомобиль клиента.

    VIN и госномер намеренно НЕ уникальные:
      - госномер меняется при продаже/регистрации,
      - VIN может быть перебит или введён с ошибкой в старой базе.
    Если сделать их unique, брат упрётся в «такой VIN уже существует»
    и не поймёт, что делать. Поэтому — только индексы для быстрого поиска.
    """

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="cars",
        verbose_name="Владелец",
    )
    brand = models.CharField("Марка", max_length=50)
    model = models.CharField("Модель", max_length=50)
    plate = models.CharField(
        "Госномер", max_length=20, db_index=True,
        validators=[validate_license_plate]
    )
    vin = models.CharField(
        "VIN", max_length=17, db_index=True,
        validators=[validate_vin]
    )
    mileage = models.PositiveIntegerField(
        "Пробег, км",
        help_text="Последнее известное значение. Уточняется при визите."
    )
    notes = models.TextField(
        "Заметка",
        blank=True,
        help_text="Видно только в CRM."
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"
        ordering = ["brand", "model"]

    def __str__(self) -> str:
        base = f"{self.brand} {self.model}"
        if self.plate:
            return f"{base} [{self.plate}]"
        return base


class WorkOrder(models.Model):
    """Заказ-наряд — работа по конкретной машине."""

    class Status(models.TextChoices):
        CREATED = "created", "Создан, ожидает решения"
        WAITING_PARTS = "waiting_parts", "Ожидание запчастей"
        WAITING_INSTALL = "waiting_install", "Ждёт установки"
        READY = "ready", "Готов"
        CANCELED = "canceled", "Отменён"

    car = models.ForeignKey(
        Car,
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="Автомобиль",
    )
    mileage = models.PositiveIntegerField(
        "Пробег при приемке, км",
        help_text="Не может быть меньше текущего пробега автомобиля."
    )
    master = models.ForeignKey(
        Master,
        on_delete=models.PROTECT,  # Нельзя удалить мастера, если на него есть заказы
        related_name="work_orders",
        verbose_name="Мастер",
    )
    status = models.CharField(
        "Статус",
        max_length=30,
        choices=Status.choices,
        default=Status.CREATED,
    )
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=20,
        choices=PAYMENT_METHODS,
        default="none"
    )
    description = models.TextField(
        "Что нужно сделать",
        help_text="Со слов клиента: «стучит спереди», «замена масла» и т. п. Видно при печати.",
    )
    notes = models.TextField(
        "Заметки мастера",
        help_text="Рекомендации. Видно при печати.",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    issued_at = models.DateTimeField(
        "Выдан",
        null=True, blank=True,
        help_text="Когда машину отдали клиенту. Заполняется автоматически при установке статуса.",
    )

    class Meta:
        verbose_name = "Заказ-наряд"
        verbose_name_plural = "Заказ-наряды"
        ordering = ["-created_at"]
        indexes = [
            # Частый запрос в CRM: «покажи новые / в работе»
            models.Index(fields=["status", "-created_at"]),
        ]

    def clean(self):
        """Валидация пробега: он не может быть меньше предыдущего."""
        super().clean()
        
        # Пропускаем проверку, если пробег не менялся (например, меняем только статус в списке)
        if self.pk and self.mileage is not None:
            old_mileage = (
                WorkOrder.objects
                .filter(pk=self.pk)
                .values_list("mileage", flat=True)
                .first()
            )
            if old_mileage == self.mileage:
                return

        # Если пробег изменился или это новый заказ — проверяем
        if self.mileage is not None and self.car_id:
            if self.mileage < self.car.mileage:
                # Важно: передаем строку, а не словарь, чтобы не было краша в list_editable
                raise ValidationError(
                    f"Пробег ({self.mileage} км) не может быть меньше "
                    f"текущего пробега автомобиля ({self.car.mileage} км)."
                )

    def save(self, *args, **kwargs):
        # Автозаполнение даты "Выдан" при статусе "Готов"
        if self.status == self.Status.READY and self.issued_at is None:
            self.issued_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Обновляем пробег самой машины, если в заказе указали больше
        if self.mileage and self.car_id and self.mileage > self.car.mileage:
            self.car.mileage = self.mileage
            self.car.save(update_fields=['mileage'])


class WorkOrderItem(models.Model):
    """Позиция в заказ-наряде: запчасть или работа."""

    class Category(models.TextChoices):
        PART = "part", "Запчасть / Расходник"
        WORK = "work", "Работа"

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ-наряд",
    )
    category = models.CharField(
        "Категория",
        max_length=20,
        choices=Category.choices,
        default=Category.PART
    )
    service = models.CharField(
        "Услуга из списка",
        max_length=50,
        blank=True,
        choices=SERVICE_CHOICES,
        help_text="Выберите, чтобы подставить название и цену."
    )
    article = models.CharField(
        "Артикул",
        max_length=50,
        blank=True,
        help_text="Оставьте пустым, если это работа (например, «Замена масла»).",
    )
    name = models.CharField(
        "Название",
        max_length=255,
        help_text="Название запчасти или работы.",
    )
    master = models.ForeignKey(
        Master, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Мастер",
        help_text="Кто выполнил эту услугу. По умолчанию берется из заказ-наряда."
    )
    quantity = models.PositiveIntegerField("Кол-во", default=1)
    purchase_price = models.DecimalField(
        "Закупочная цена",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Видно только в CRM. На печать для клиента не попадает.",
    )
    client_price = models.DecimalField(
        "Цена для клиента",
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.name} (x{self.quantity})"

    @property
    def total_client_price(self):
        """Сумма для клиента: цена × количество."""
        return self.client_price * self.quantity

    def save(self, *args, **kwargs):
        """Автоматически подставляем мастера из заказа, если он не указан."""
        if not self.master_id and self.work_order_id and self.category == self.Category.WORK:
            self.master = self.work_order.master
        super().save(*args, **kwargs)


class WarehouseItem(models.Model):
    """Склад автосервиса."""

    article = models.CharField("Артикул", max_length=50)
    name = models.CharField("Наименование", max_length=255)
    purchase_price = models.DecimalField(
        "Закупочная цена", max_digits=10, decimal_places=2
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    note = models.TextField(
        "Заметка", blank=True, 
        help_text="Видно только в CRM."
    )
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Запчасть на складе"
        verbose_name_plural = "Склад"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.article} — {self.name} ({self.quantity} шт.)"