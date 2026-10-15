from django.shortcuts import render

def home(request):
    """Главная страница."""
    return render(request, "home.html")
