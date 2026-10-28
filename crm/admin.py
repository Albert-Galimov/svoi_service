import unfold

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

# Импортируем все модели, включая новую WarehouseItem
from .models import Car, Master, Client, WorkOrder, WorkOrderItem, WarehouseItem


# ==========================================
# INLINES (Отображение связей внутри карточек)
# ==========================================

class CarInline(unfold.admin.TabularInline):
    """Показывает машины внутри карточки клиента (только чтение, в виде таблицы)."""
    model = Car
    extra = 0
    
    # Используем кастомные методы вместо реальных полей
    fields = ("brand_link", "model_link", "plate_link", "vin_link", "mileage_link")
    readonly_fields = fields
    
    # Отключаем стандартную кнопку "Изменить" и заголовок
    show_change_link = False 
    
    # Запрещаем удалять прямо отсюда
    can_delete = False
    
    ordering = ("brand", "model")

    # Отключаем добавление новых машин
    def has_add_permission(self, request, obj=None):
        return False

    # Отключаем редактирование
    def has_change_permission(self, request, obj=None):
        return False

    # --- Вспомогательный метод для генерации ссылки ---
    def _get_link(self, obj, text):
        """Оборачивает текст в ссылку на редактирование авто."""
        if not obj.pk:
            return text
        url = reverse("admin:crm_car_change", args=[obj.pk])
        # display: block делает так, чтобы клик срабатывал по всей ячейке
        return format_html(
            '<a href="{}" style="display: block; width: 100%; height: 100%;">{}</a>', 
            url, text
        )

    # --- Кастомные методы для полей ---
    @admin.display(description="Марка")
    def brand_link(self, obj):
        return self._get_link(obj, obj.brand)

    @admin.display(description="Модель")
    def model_link(self, obj):
        return self._get_link(obj, obj.model)

    @admin.display(description="Госномер")
    def plate_link(self, obj):
        return self._get_link(obj, obj.plate)

    @admin.display(description="VIN")
    def vin_link(self, obj):
        return self._get_link(obj, obj.vin)

    @admin.display(description="Пробег, км")
    def mileage_link(self, obj):
        return self._get_link(obj, obj.mileage)


class WorkOrderInline(unfold.admin.TabularInline):
    """Показывает заказ-наряды внутри карточки автомобиля (только чтение)."""
    model = WorkOrder
    extra = 0
    
    # Используем кастомные методы для кликабельности
    fields = ("id_link", "status_link", "created_at_link", "description_link")
    readonly_fields = fields
    
    show_change_link = False  # Отключаем стандартную кнопку "Изменить"
    can_delete = False        # Запрещаем удаление
    ordering = ("-created_at",)  # От новых к старым

    # Отключаем добавление новых заказов из карточки авто
    def has_add_permission(self, request, obj=None):
        return False

    # Отключаем редактирование прямо в таблице
    def has_change_permission(self, request, obj=None):
        return False

    # --- Вспомогательный метод для генерации ссылки ---
    def _get_link(self, obj, text):
        """Оборачивает текст в ссылку на редактирование заказа."""
        if not obj.pk:
            return text
        url = reverse("admin:crm_workorder_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display: block; width: 100%; height: 100%;">{}</a>', 
            url, text
        )

    # --- Кастомные методы для полей ---
    @admin.display(description="Заказ", ordering="id")
    def id_link(self, obj):
        return self._get_link(obj, f"№{obj.pk}")

    @admin.display(description="Статус", ordering="status")
    def status_link(self, obj):
        return self._get_link(obj, obj.get_status_display())

    @admin.display(description="Дата", ordering="created_at")
    def created_at_link(self, obj):
        # Форматируем дату, чтобы она не была слишком длинной
        date_str = obj.created_at.strftime("%d.%m.%Y %H:%M")
        return self._get_link(obj, date_str)

    @admin.display(description="Описание")
    def description_link(self, obj):
        # Если описание очень длинное, можно его обрезать
        desc = obj.description
        if len(desc) > 50:
            desc = desc[:50] + "..."
        return self._get_link(obj, desc)


class WorkOrderItemInline(unfold.admin.TabularInline):
    """Позиции (запчасти и работы) внутри заказ-наряда."""
    model = WorkOrderItem
    extra = 1
    fields = ("article", "name", "quantity", "purchase_price", "client_price")
    ordering = ("id",)

    class Media:
        js = ("js/admin_parts.js",)


# ==========================================
# АДМИНКИ МОДЕЛЕЙ
# ==========================================

@admin.register(Client)
class ClientAdmin(unfold.admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    list_display_links = ("name", "phone", "created_at")
    search_fields = ("name", "phone", "notes")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    
    # ДОБАВЛЕНО: Машины отображаются внутри клиента
    inlines = [CarInline]

    fieldsets = (
        ("Клиент", {"fields": ("name", "phone")}),
        ("Дополнительно", {"fields": ("notes",)}),
        ("Служебное", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Car)
class CarAdmin(unfold.admin.ModelAdmin):
    list_display = ("__str__", "client", "vin", "plate", "mileage")
    list_display_links = ("__str__", "client", "vin", "plate", "mileage")
    list_filter = ("brand",)
    search_fields = (
        "plate", "vin", "brand", "model",
        "client__name", "client__phone",
    )
    autocomplete_fields = ("client",)
    readonly_fields = ("created_at", "updated_at")
    
    # ДОБАВЛЕНО: Заказ-наряды отображаются внутри машины
    inlines = [WorkOrderInline]

    fieldsets = (
        ("Владелец", {"fields": ("client",)}),
        ("Автомобиль", {"fields": ("brand", "model", "plate", "vin", "mileage")}),
        ("Дополнительно", {"fields": ("notes",)}),  # Вынес из 'Служебного', чтобы было видно
        ("Служебное", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Master)
class MasterAdmin(unfold.admin.ModelAdmin):
    list_display = ("name", "is_active")
    ordering = ("name",)


@admin.register(WorkOrder)
class WorkOrderAdmin(unfold.admin.ModelAdmin):
    list_display = ("car", "master", "status", "created_at", "issued_at", "print_button")
    list_display_links = ("car", "master", "created_at", "issued_at")
    list_filter = ("status", "master", "created_at")
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
    change_form_template = "admin/crm/workorder/change_form.html"

    fieldsets = (
        ("Автомобиль", {"fields": ("car", "mileage")}),
        ("Исполнение", {"fields": ("master", "payment_method")}),
        ("Работа", {"fields": ("status", "description", "notes")}),
        ("Сроки", {"fields": ("issued_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # Подключаем наш JS
    class Media:
        js = ("js/admin_car_notes.js",)

    def print_button(self, obj):
        """Генерирует ссылку-кнопку для перехода на страницу печати."""
        if obj.pk:
            url = reverse("crm:work_order_print", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color: #e87722; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-weight: bold;">🖨️ Печать</a>', 
                url
            )
        return "—"
    
    print_button.short_description = "Прайс"


@admin.register(WarehouseItem)
class WarehouseItemAdmin(unfold.admin.ModelAdmin):
    """Админка для раздела 'Склад'."""
    list_display = ("article", "name", "quantity", "purchase_price", "updated_at")
    search_fields = ("article", "name", "note")
    list_editable = ("quantity", "purchase_price")
    ordering = ("-updated_at",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Информация о запчасти", {
            "fields": ("article", "name", "quantity", "purchase_price")
        }),
        ("Дополнительно", {
            "fields": ("note",)
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )