import logging

from django.shortcuts import redirect, render

from core.constants import CONTACTS, SERVICES
from core.forms import BookingForm
from notifications.service import notify_about_booking

logger = logging.getLogger(__name__)


def home(request):
    """Главная страница: лендинг + форма заявки."""
    context = {
        "services": SERVICES,
        "contacts": CONTACTS,
        "form": BookingForm(),
    }
    return render(request, "home.html", context)


def booking_create(request):
    if request.method != "POST":
        return redirect("public:home")

    form = BookingForm(request.POST)
    if form.is_valid():
        booking = form.save()

        try:
            notify_about_booking(booking)
        except Exception:
            logger.exception(
                "Неожиданная ошибка при отправке уведомления в ВК "
                "о заявке id=%s",
                booking.pk,
            )

        return redirect("public:thanks")

    context = {
        "services": SERVICES,
        "contacts": CONTACTS,
        "form": form,
        "scroll_to": "booking",
    }
    return render(request, "home.html", context)


def thanks(request):
    """Страница благодарности после отправки заявки."""
    return render(request, "thanks.html", {"contacts": CONTACTS})
