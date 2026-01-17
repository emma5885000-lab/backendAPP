from django.contrib import admin
from .models import HealthData


@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'heart_rate', 'oxygen_level', 'temperature', 'respiratory_rate', 'air_quality', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
