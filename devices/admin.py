from django.contrib import admin
from .models import Device, SensorData


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'device_key_short', 'is_active', 'created_at', 'last_data_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username', 'user__email', 'device_key')
    readonly_fields = ('id', 'device_key', 'created_at', 'last_data_at')
    ordering = ('-created_at',)
    
    def device_key_short(self, obj):
        return f"{obj.device_key[:16]}..."
    device_key_short.short_description = 'Device Key'


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'heart_rate', 'spo2', 'temperature', 'ai_status_name', 'ai_confidence', 'created_at')
    list_filter = ('ai_status', 'processed', 'created_at')
    search_fields = ('device__name', 'device__user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Device', {'fields': ('device',)}),
        ('Données Capteur', {'fields': ('cov_ppb', 'eco2_ppm', 'heart_rate', 'spo2', 'temperature')}),
        ('Résultat IA', {'fields': ('ai_status', 'ai_status_name', 'ai_confidence', 'ai_probabilities', 'processed')}),
        ('Métadonnées', {'fields': ('created_at',)}),
    )
