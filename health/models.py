from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class HealthData(models.Model):
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('attention', 'Attention'),
        ('danger', 'Danger'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_data')
    heart_rate = models.IntegerField(help_text="Fréquence cardiaque (bpm)")
    oxygen_level = models.FloatField(help_text="SpO2 (%)")
    temperature = models.FloatField(help_text="Température corporelle (°C)")
    respiratory_rate = models.IntegerField(default=16, help_text="Fréquence respiratoire (/min)")
    air_quality = models.IntegerField(default=35, help_text="Qualité de l'air (AQI)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Santé {self.user} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    def get_status_display_fr(self):
        status_map = {
            'normal': 'Normal',
            'attention': 'Attention',
            'danger': 'Danger'
        }
        return status_map.get(self.status, 'Normal')
