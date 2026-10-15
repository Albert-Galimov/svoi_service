from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("", views.home, name="home"),
    path("booking/", views.booking_create, name="booking_create"),
    path("thanks/", views.thanks, name="thanks"),
]