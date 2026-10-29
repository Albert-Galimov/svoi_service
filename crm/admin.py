import unfold

from django import forms
from django.contrib import admin
from django.forms.models import construct_instance # <-- Импортируем функцию для обновления объекта
from django.urls import reverse
from django.utils.html import format_html

from .models import Car, Master, Client, WorkOrder, WorkOrderItem, WarehouseItem


# ==========================================
# INLINES (Отображение связей внутри карточек)
# ==========================================

class CarInline(unfold.admin.TabularInline):
    """Показывает машины внутри карточки клиента (только чтение, в виде таблицы)."""
    model = Car
    extra = 0
    fields = ("brand_link", "model_link", "plate_link", "vin_link", "mileage_link")
    readonly_fields = fields
    show_change_link = False 
    can_delete = False
    ordering = ("brand", "model")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _get_link(self, obj, text):
        if not obj.pk:
            return text
        url = reverse("admin:crm_car_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display: block; width: 100%; height: 100%;">{}</a>', 
            url, text
        )

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
    fields = ("id_link", "status_link", "created_at_link", "description_link")
    readonly_fields = fields
    show_change_link = False
    can_delete = False
    ordering = ("-created_at",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _get_link(self, obj, text):
        if not obj.pk:
            return text
        url = reverse("admin:crm_workorder_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display: block; width: 100%; height: 100%;">{}</a>', 
            url, text
        )

    @admin.display(description="Заказ", ordering="id")
    def id_link(self, obj):
        return self._get_link(obj, f"№{obj.pk}")

    @admin.display(description="Статус", ordering="status")
    def status_link(self, obj):
        return self._get_link(obj, obj.get_status_display())

    @admin.display(description="Дата", ordering="created_at")
    def created_at_link(self, obj):
        date_str = obj.created_at.strftime("%d.%m.%Y %H:%M")
        return self._get_link(obj, date_str)

    @admin.display(description="Описание")
    def description_link(self, obj):
        desc = obj.description
        if len(desc) > 50:
            desc = desc[:50] + "..."
        return self._get_link(obj, desc)


class BaseWorkOrderItemInline(unfold.admin.TabularInline):
    model = WorkOrderItem
    extra = 1
    category_value = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.category_value:
            return qs.filter(category=self.category_value)
        return qs

    def get_formset(self, request, obj=None, **kwargs):
        BaseFormSet = super().get_formset(request, obj, **kwargs)
        category = self.category_value

        class CategorizedFormSet(BaseFormSet):
            def save_new(self, form, commit=True):
                instance = super().save_new(form, commit=False)
                instance.category = category
                if commit:
                    instance.save()
                    form.save_m2m()
                return instance

            def save_existing(self, form, instance, commit=True):
                instance.category = category
                return super().save_existing(form, instance, commit)

        return CategorizedFormSet


class WorkOrderPartInline(BaseWorkOrderItemInline):
    category_value = WorkOrderItem.Category.PART
    fields = ("article", "name", "quantity", "purchase_price", "client_price")
    verbose_name = "Запчасть"
    verbose_name_plural = "Запчасти и расходники"
    class Media:
        js = ("js/admin_parts.js",)


class WorkOrderWorkInline(BaseWorkOrderItemInline):
    category_value = WorkOrderItem.Category.WORK
    fields = ("service", "name", "master", "quantity", "client_price")
    verbose_name = "Услуга"
    verbose_name_plural = "Работы и услуги"
    class Media:
        js = ("js/admin_services.js",)


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
    inlines = [WorkOrderInline]

    fieldsets = (
        ("Владелец", {"fields": ("client",)}),
        ("Автомобиль", {"fields": ("brand", "model", "plate", "vin", "mileage")}),
        ("Дополнительно", {"fields": ("notes",)}),
        ("Служебное", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Master)
class MasterAdmin(unfold.admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",) # ДОБАВИЛИ ПОИСК ДЛЯ АВТОДОПОЛНЕНИЯ
    ordering = ("name",)


class WorkOrderChangelistForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = "__all__"

    def _post_clean(self):
        """Обновляем объект, но пропускаем вызов Model.clean() (валидацию пробега)."""
        # Эта строка применяет изменения из формы к объекту (в т.ч. новый статус)
        self.instance = construct_instance(self, self.instance, self._meta.fields, self._meta.exclude)
        # Мы намеренно не вызываем self.instance.full_clean(), 
        # чтобы Django не проверял пробег при смене статуса в списке.


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
    # ДОБАВИЛИ "master" СЮДА
    autocomplete_fields = ("car", "master") 
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [WorkOrderPartInline, WorkOrderWorkInline]
    change_form_template = "admin/crm/workorder/change_form.html"

    fieldsets = (
        ("Автомобиль", {"fields": ("car", "mileage")}),
        ("Исполнение", {"fields": ("master", "payment_method")}),
        ("Работа", {"fields": ("status", "description", "notes")}),
        ("Сроки", {"fields": ("issued_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    class Media:
        js = ("js/admin_car_notes.js",)

    def get_changelist_form(self, request, **kwargs):
        return WorkOrderChangelistForm

    def print_button(self, obj):
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