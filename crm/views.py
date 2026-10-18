from django.shortcuts import render

# crm/views.py
from public.models import Booking
from .models import Client, WorkOrder

def dashboard_callback(request, context):
    """Собирает статистику для главной страницы админки."""
    context.update({
        "total_clients": Client.objects.count(),
        "new_bookings": Booking.objects.filter(status=Booking.Status.NEW).count(),
        "active_orders": WorkOrder.objects.filter(
            status__in=[WorkOrder.Status.IN_PROGRESS, WorkOrder.Status.WAITING_PARTS]
        ).count(),
        "recent_bookings": Booking.objects.order_by("-created_at")[:5],
    })
    return context
