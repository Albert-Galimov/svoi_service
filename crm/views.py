from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Sum
from django.template.loader import render_to_string

from public.models import Booking
from .models import Client, WorkOrder, WarehouseItem
from core.constants import PART_SUPPLIER_URLS, CONTACTS


def dashboard_callback(request, context):
    """Собирает статистику для главной страницы админки."""
    context.update({
        "total_clients": Client.objects.count(),
        "new_bookings": Booking.objects.filter(status=Booking.Status.NEW).count(),
        "active_orders": WorkOrder.objects.filter(
            status__in=[WorkOrder.Status.WAITING_INSTALL, WorkOrder.Status.WAITING_PARTS]
        ).count(),
        "recent_bookings": Booking.objects.order_by("-created_at")[:5],
    })
    return context


@login_required
@require_GET
def part_lookup_api(request):
    """Принимает артикул, возвращает ссылки на поставщиков и остаток на складе."""
    article = request.GET.get("article", "").strip().upper()
    
    if not article:
        return JsonResponse({"suppliers": [], "stock": 0})

    # 1. Ищем остаток на складе (суммируем, если вдруг несколько партий одной детали)
    stock_data = WarehouseItem.objects.filter(
        article__iexact=article  # Ищем без учета регистра
    ).aggregate(total=Sum('quantity'))
    
    stock = stock_data['total'] or 0

    # 2. Формируем ссылки на поставщиков
    suppliers = []
    for supplier_name, url_template in PART_SUPPLIER_URLS.items():
        suppliers.append({
            "name": supplier_name,
            "url": url_template.format(article=article)
        })

    return JsonResponse({
        "article": article,
        "suppliers": suppliers,
        "stock": stock  # <-- Возвращаем остаток
    })


@login_required
def work_order_print(request, pk):
    """Страница печати прайса для клиента.

    Показываем только client_price и итоговую сумму.
    purchase_price (закупочная цена) на печать НЕ попадает.
    """
    order = get_object_or_404(WorkOrder, pk=pk)
    items = order.items.all()
    
    # Считаем итог для клиента
    total = sum(item.total_client_price for item in items)

    context = {
        "order": order,
        "items": items,
        "total": total,
        "contacts": CONTACTS,
    }
    return render(request, "work_order_print.html", context)


@login_required
@require_GET
def car_notes_api(request):
    """Возвращает HTML-блок с прошлыми заметками мастера для выбранного авто."""
    car_id = request.GET.get("car_id")
    exclude_id = request.GET.get("exclude_id")

    if not car_id:
        return JsonResponse({"html": ""})

    # Ищем заказы этой машины, где есть заметки
    qs = WorkOrder.objects.filter(car_id=car_id).exclude(notes="").exclude(notes__isnull=True)
    
    # Если редактируем существующий заказ, исключаем его из списка "прошлых"
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)

    # Берем 5 последних
    previous_notes = qs.order_by("-created_at")[:5]

    # Рендерим HTML через отдельный партиал-шаблон
    html = render_to_string(
        "admin/crm/workorder/previous_notes_block.html", 
        {"previous_notes": previous_notes}
    )

    return JsonResponse({"html": html})
