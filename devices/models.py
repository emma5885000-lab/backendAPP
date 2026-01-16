from django.db import models
from django.conf import settings
import uuid


class Device(models.Model):
    """Équipement hardware lié à un utilisateur"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    name = models.CharField(max_length=100, default='Capteur HealthTic')
    device_key = models.CharField(max_length=64, unique=True)  # Clé d'authentification du device
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_data_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class SensorData(models.Model):
    """Données brutes reçues du capteur hardware"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sensor_data')
    
    # Données du capteur
    cov_ppb = models.FloatField(help_text="COV en ppb")
    eco2_ppm = models.FloatField(help_text="eCO2 en ppm")
    heart_rate = models.FloatField(help_text="Fréquence cardiaque")
    spo2 = models.FloatField(help_text="Saturation en oxygène")
    temperature = models.FloatField(help_text="Température corporelle")
    
    # Résultat de l'analyse IA
    ai_status = models.IntegerField(null=True, blank=True, help_text="0=Sain, 1=Infection légère, 2=Infection modérée, 3=Hypoxie sévère")
    ai_status_name = models.CharField(max_length=50, null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True, help_text="Confiance de l'IA en %")
    ai_probabilities = models.JSONField(null=True, blank=True, help_text="Probabilités pour chaque classe")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Data {self.device.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
