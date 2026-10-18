"""Модели CRM автосервиса.

Схема связей:

    Client ←(1:N)— Car ←(1:N)— WorkOrder

  - у клиента может быть несколько машин (он и жена ездят),
  - у машины может быть несколько заказ-нарядов за всю историю.

Клиент из заказ-наряда достаётся через `order.car.client`.
"""

from django.db import models

from core.fields import PhoneField


class Client(models.Model):
    """Клиент автосервиса.

    Ключ поиска — телефон. Один клиент = один нормализованный номер.
    Если человек с тем же телефоном уже есть — Django не даст создать
    дубль (unique=True), и это правильно.
    """

    name = models.CharField("Имя", max_length=100)
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
        "Госномер", max_length=20, blank=True, db_index=True
    )
    vin = models.CharField(
        "VIN", max_length=17, blank=True, db_index=True
    )
    mileage = models.PositiveIntegerField(
        "Пробег, км", null=True, blank=True,
        help_text="Последнее известное значение. Уточняется при визите.",
    )
    notes = models.TextField("Заметки", blank=True)
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
    """Заказ-наряд — работа по конкретной машине.

    Статусы описывают жизненный цикл: от приёмки до выдачи.
    Позиции (запчасти и работы) появятся на следующем этапе.
    """

    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        IN_PROGRESS = "in_progress", "В работе"
        WAITING_PARTS = "waiting_parts", "Ожидание запчастей"
        READY = "ready", "Готов"
        CANCELED = "canceled", "Отменён"

    car = models.ForeignKey(
        Car,
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="Автомобиль",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
    )
    description = models.TextField(
        "Что нужно сделать",
        help_text="Со слов клиента: «стучит спереди», «замена масла» и т. п.",
    )
    notes = models.TextField(
        "Заметки мастера",
        blank=True,
        help_text="Наблюдения по ходу работ. Видно только в CRM.",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    issued_at = models.DateTimeField(
        "Выдан",
        null=True, blank=True,
        help_text="Заполняется, когда машину отдали клиенту.",
    )

    class Meta:
        verbose_name = "Заказ-наряд"
        verbose_name_plural = "Заказ-наряды"
        ordering = ["-created_at"]
        indexes = [
            # Частый запрос в CRM: «покажи новые / в работе»
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"№{self.pk or '—'} · {self.car} · {self.get_status_display()}"
