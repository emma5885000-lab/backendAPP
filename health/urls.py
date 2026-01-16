from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthDataViewSet

router = DefaultRouter()
router.register('', HealthDataViewSet, basename='health')

urlpatterns = [
    path('', include(router.urls)),
]
