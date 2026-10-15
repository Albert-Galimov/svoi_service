import re

from django.core.exceptions import ValidationError


# Всё, что не цифра, — выкидываем при нормализации.
_NON_DIGIT_RE = re.compile(r"\D+")


def normalize_phone(value: str) -> str:
    """Приводит телефон к каноническому виду +7XXXXXXXXXX."""

    if not value:
        return ""

    digits = _NON_DIGIT_RE.sub("", value)

    if len(digits) == 11 and digits[0] == "8":
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits

    return f"+{digits}" if digits else ""


def validate_russian_phone(value: str) -> None:
    """Проверяет, что номер — российский.

    Ожидаемый вид: +7 и ровно 10 цифр (например, +79171234567).
    """
    if not value:
        return

    normalized = normalize_phone(value)

    if not re.fullmatch(r"\+7\d{10}", normalized):
        raise ValidationError(
            "Введите российский номер: +7 и 10 цифр. "
            "Пример: +7 917 123-45-67."
        )
