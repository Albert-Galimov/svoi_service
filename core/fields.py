"""Кастомные поля для моделей Django."""

from django.db import models

from .validators import normalize_phone, validate_russian_phone


class PhoneField(models.CharField):
    """CharField, который хранит телефон в формате +7XXXXXXXXXX."""

    description = "Телефон в формате +7XXXXXXXXXX"
    default_validators = [validate_russian_phone]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 12)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        return normalize_phone(value)

    def to_python(self, value):
        if value in (None, ""):
            return value
        return normalize_phone(value)

    def get_prep_value(self, value):
        if value in (None, ""):
            return value
        return normalize_phone(value)
