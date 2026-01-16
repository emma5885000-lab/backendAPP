from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/users/', include('users.urls')),
    path('api/health/', include('health.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/devices/', include('devices.urls')),
    path('api/', include('measurements.urls')),
    
]
