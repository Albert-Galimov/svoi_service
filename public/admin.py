from django.contrib import admin

from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "phone", "status")
    list_filter = ("status", "created_at")
    search_fields = ("name", "phone")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "processed_at")
    list_editable = ("status",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Клиент", {
            "fields": ("name", "phone")
        }),
        ("Работа владельца", {
            "fields": ("status", "notes", "processed_at")
        }),
        ("Служебное", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )
