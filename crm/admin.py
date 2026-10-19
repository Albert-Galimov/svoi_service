"""Админка CRM.

Ключевые фичи:
  - поиск по телефону клиента и госномеру/VIN машины;
  - autocomplete для связей: брат начинает вводить «А123» — Django
    подсказывает машины, а не заставляет выбирать из выпадающего списка
    на 500 позиций;
  - смена статуса заказ-наряда прямо из списка (list_editable).
"""
import unfold

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Car, Client, WorkOrder, WorkOrderItem


@admin.register(Client)
class ClientAdmin(unfold.admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    list_display_links = ("name", "phone", "created_at", )
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
class CarAdmin(unfold.admin.ModelAdmin):
    list_display = ("__str__", "client", "vin", "plate", "mileage")
    list_display_links = ("__str__", "client", "vin", "plate", "mileage", )
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


class WorkOrderItemInline(admin.TabularInline):
    """Позиции (запчасти и работы) внутри заказ-наряда."""
    model = WorkOrderItem
    extra = 1
    fields = ("article", "name", "quantity", "purchase_price", "client_price")
    ordering = ("id",)

    class Media:
        # Django подключит static/js/admin_parts.js на странице с этим inline.
        js = ("js/admin_parts.js",)


@admin.register(WorkOrder)
class WorkOrderAdmin(unfold.admin.ModelAdmin):
    list_display = ("id", "car", "status", "created_at", "issued_at", "print_button")
    list_display_links = ("id", "car", "created_at", "issued_at", )
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
    inlines = [WorkOrderItemInline]

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

    def print_button(self, obj):
        """Генерирует ссылку-кнопку для перехода на страницу печати."""
        if obj.pk:
            url = reverse("crm:work_order_print", args=[obj.pk])
            # target="_blank" открывает печать в новой вкладке
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color: #e87722; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-weight: bold;">🖨️ Печать</a>', 
                url
            )
        return "—"
    
    print_button.short_description = "Прайс"
