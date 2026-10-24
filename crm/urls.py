from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("api/part-lookup/", views.part_lookup_api, name="part_lookup_api"),
    path("work-order/<int:pk>/print/", views.work_order_print, name="work_order_print"),
]
