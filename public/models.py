from django.db import models

from core.fields import PhoneField


class Booking(models.Model):
    """Заявка на запись с сайта."""

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        CALLED = "called", "Позвонили"
        SCHEDULED = "sheduled", "Записан"
        DECLINED = "declined", "Отказ"

    name = models.CharField("Имя", max_length=100)
    phone = PhoneField("Телефон")

    # --- Что добавляет владелец сервиса ---
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    notes = models.TextField(
        "Заметки владельца",
        blank=True,
        help_text="Видно только в CRM, клиенту не показывается.",
    )

    # --- Служебное ---
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    processed_at = models.DateTimeField("Обработана", null=True, blank=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone} - ({self.get_status_display()})"
