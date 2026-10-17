import logging

from django.shortcuts import redirect, render

from core.constants import CONTACTS, SERVICES

from core.forms import BookingForm

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
    """Приём заявки с формы. Только POST."""
    # Если кто-то открыл URL руками (GET) — просто на главную.
    if request.method != "POST":
        return redirect("public:home")

    form = BookingForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("public:thanks")

    # Если форма не прошла валидацию — возвращаем на главную с ошибками.
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
