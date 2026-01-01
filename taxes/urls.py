from django.urls import path
from . import views

urlpatterns = [
    path('', views.taxes_dashboard, name='taxes_dashboard'),
]
