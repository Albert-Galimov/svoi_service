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


def validate_license_plate(value: str) -> None:
    """Проверяет российский госномер.
    
    Примеры: А123ВС77, В777АА116, Е001КХ777.
    Допускаются кириллические буквы, цифры и пробелы.
    """
    if not value:
        return
    # Приводим к верхнему регистру и убираем лишние пробелы
    value = re.sub(r"\s+", "", value).upper()
    # Регулярка для российских номеров (тип 1 и тип 1А)
    if not re.fullmatch(r"[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}", value):
        raise ValidationError(
            "Некорректный госномер. Пример: А123ВС77 или А123ВС777."
        )


def validate_vin(value: str) -> None:
    """Проверяет VIN на соответствие стандарту.
    
    VIN состоит ровно из 17 символов (латиница и цифры).
    Буквы I, O, Q не используются, чтобы не путать с 1 и 0.
    """
    if not value:
        return
    value = value.upper()
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", value):
        raise ValidationError(
            "VIN должен состоять из 17 символов (латинские буквы и цифры, "
            "без букв I, O, Q)."
        )
