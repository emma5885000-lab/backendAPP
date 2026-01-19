from django.urls import path
from . import views

urlpatterns = [
    # Endpoints pour le hardware (authentification via device_key)
    path('data/', views.receive_sensor_data, name='receive_sensor_data'),
    path('hardware/data/', views.receive_sensor_data, name='hardware_receive_sensor_data'),  # Alias pour l'ESP32
    
    # Endpoints pour l'utilisateur (authentification via token)
    path('my-devices/', views.my_devices, name='my_devices'),
    path('create/', views.create_device, name='create_device'),
    path('<uuid:device_id>/', views.get_device, name='get_device'),
    path('<uuid:device_id>/update/', views.update_device, name='update_device'),
    path('<uuid:device_id>/delete/', views.delete_device, name='delete_device'),
    path('<uuid:device_id>/regenerate-key/', views.regenerate_device_key, name='regenerate_device_key'),
    path('sensor-data/', views.my_sensor_data, name='my_sensor_data'),
    path('latest-ai/', views.latest_ai_result, name='latest_ai_result'),
]
