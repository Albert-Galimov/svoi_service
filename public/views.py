from django.shortcuts import render, redirect

from core.constants import SERVICES, CONTACTS
from core.forms import BookingForm

def home(request):
    """Главная страница. Лендинг"""
    context = {
        "services": SERVICES,
        "contacts": CONTACTS,
        "form": BookingForm(),
    }
    return render(request, "home.html", context)

def booking_create(request):
    """Приём заявки с формы. Только POST."""
    # Если кто-то открыл URL в браузере напрямую (GET) — просто на главную.
    if request.method != "POST":
        return redirect("public:home")

    form = BookingForm(request.POST)
    if form.is_valid():
        form.save()
        # PRG-паттерн: после успешной отправки перенаправляем,
        # чтобы F5 не отправлял заявку повторно.
        return redirect("public:thanks")

    # Если форма не прошла валидацию — возвращаем на главную с ошибками.
    context = {
        "services": SERVICES,
        "contacts": CONTACTS,
        "form": form,
        "scroll_to": "booking",  # подсказка шаблону, куда прокрутить
    }
    return render(request, "home.html", context)


def thanks(request):
    """Страница благодарности после отправки заявки."""
    return render(request, "thanks.html", {"contacts": CONTACTS})
