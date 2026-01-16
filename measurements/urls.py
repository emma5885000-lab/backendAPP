# measurements/urls.py
from django.urls import path
from .views import MeasurementAPIView

urlpatterns = [
    path('measurements/', MeasurementAPIView.as_view(), name='measurements'),
]
