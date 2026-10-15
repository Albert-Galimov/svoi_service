from django.shortcuts import render

from core.constants import SERVICES, CONTACTS

def home(request):
    """Главная страница. Лендинг"""
    context = {
        "services": SERVICES,
        "contacts": CONTACTS,
    }
    return render(request, "home.html", context)
