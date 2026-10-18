"""Админка CRM.

Ключевые фичи:
  - поиск по телефону клиента и госномеру/VIN машины;
  - autocomplete для связей: брат начинает вводить «А123» — Django
    подсказывает машины, а не заставляет выбирать из выпадающего списка
    на 500 позиций;
  - смена статуса заказ-наряда прямо из списка (list_editable).
"""

from django.contrib import admin

from .models import Car, Client, WorkOrder


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    search_fields = ("name", "phone", "notes")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("Клиент", {
            "fields": ("name", "phone")
        }),
        ("Заметки", {
            "fields": ("notes",)
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("__str__", "client", "vin", "plate", "mileage")
    list_filter = ("brand",)
    # Поиск работает и по связанной модели (client__phone) —
    # брат вводит номер и сразу видит все машины этого человека.
    search_fields = (
        "plate", "vin", "brand", "model",
        "client__name", "client__phone",
    )
    autocomplete_fields = ("client",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Владелец", {
            "fields": ("client",)
        }),
        ("Автомобиль", {
            "fields": ("brand", "model", "plate", "vin", "mileage")
        }),
        ("Служебное", {
            "fields": ("notes", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "status", "created_at", "issued_at")
    list_filter = ("status", "created_at")
    # list_editable требует, чтобы поле было в list_display,
    # но НЕ первым (первое — это ссылка на редактирование).
    list_editable = ("status",)
    search_fields = (
        "car__plate", "car__vin", "car__brand", "car__model",
        "car__client__name", "car__client__phone",
        "description",
    )
    autocomplete_fields = ("car",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("Автомобиль", {
            "fields": ("car",)
        }),
        ("Работа", {
            "fields": ("status", "description", "notes")
        }),
        ("Сроки", {
            "fields": ("issued_at", "created_at", "updated_at")
        }),
    )
