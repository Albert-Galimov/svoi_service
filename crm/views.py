from datetime import date
from django.utils.dateparse import parse_date
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Sum, F
from django.template.loader import render_to_string

from public.models import Booking
from .models import Client, WorkOrder, WarehouseItem, Master, WorkOrderItem
from core.constants import PART_SUPPLIER_URLS, CONTACTS, SERVICES

@login_required
def dashboard_callback(request, context):
    """Собирает статистику для главной страницы админки."""
    
    # --- 1. Базовые данные (как было раньше) ---
    context.update({
        "total_clients": Client.objects.count(),
        "new_bookings": Booking.objects.filter(status=Booking.Status.NEW).count(),
        "active_orders": WorkOrder.objects.filter(
            status__in=[WorkOrder.Status.WAITING_PARTS, WorkOrder.Status.WAITING_INSTALL]
        ).count(),
        "recent_bookings": Booking.objects.order_by("-created_at")[:5],
        "masters": Master.objects.filter(is_active=True),
    })

    # --- 2. Финансовая статистика ---
    today = date.today()
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    master_id = request.GET.get("master_id")

    # Если даты не выбраны, ставим период: с 1-го числа текущего месяца по сегодня
    if start_date_str:
        start_date = parse_date(start_date_str)
    else:
        start_date = today.replace(day=1)

    if end_date_str:
        end_date = parse_date(end_date_str)
    else:
        end_date = today

    context.update({
        "start_date": start_date,
        "end_date": end_date,
        "selected_master_id": int(master_id) if master_id else None,
    })

    # Берем заказы за выбранный период, исключая отмененные
    orders_in_period = WorkOrder.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).exclude(status='canceled')

    # Берем все позиции из этих заказов
    items_in_period = WorkOrderItem.objects.filter(work_order__in=orders_in_period)

    # Выражение для подсчета суммы: цена * количество
    revenue_expr = Sum(F('client_price') * F('quantity'))

    # Считаем выручку по категориям
    parts_revenue = items_in_period.filter(category='part').aggregate(total=revenue_expr)['total'] or 0
    services_revenue = items_in_period.filter(category='work').aggregate(total=revenue_expr)['total'] or 0

    context.update({
        "parts_revenue": parts_revenue,
        "services_revenue": services_revenue,
        "total_revenue": parts_revenue + services_revenue,
    })

    # Считаем выручку конкретного мастера (только за работы)
    if master_id:
        master_revenue = items_in_period.filter(
            category='work', 
            master_id=master_id
        ).aggregate(total=revenue_expr)['total'] or 0
        context["master_revenue"] = master_revenue

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
@require_GET
def service_lookup_api(request):
    """Возвращает название и цену выбранной услуги из констант."""
    service_code = request.GET.get("code")
    if not service_code:
        return JsonResponse({"name": "", "price": 0})

    service_data = SERVICES.get(service_code)
    if service_data:
        return JsonResponse({
            "name": service_data["name"],
            "price": str(service_data["price"])
        })
    return JsonResponse({"name": "", "price": 0})


@login_required
def work_order_print(request, pk):
    """Страница печати прайса для клиента."""
    order = get_object_or_404(WorkOrder, pk=pk)
    
    # Разделяем на группы
    parts_and_consumables = order.items.filter(category='part')
    works = order.items.filter(category='work')
    
    # Считаем общий итог (по всем позициям)
    total = sum(item.total_client_price for item in order.items.all())

    context = {
        "order": order,
        "parts_and_consumables": parts_and_consumables,
        "works": works,
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
