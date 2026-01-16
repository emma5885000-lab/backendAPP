from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
import secrets

from .models import Device, SensorData
from .ai_service.medical_classifier import predict_health_status
from health.models import HealthData


@api_view(['POST'])
@permission_classes([AllowAny])  # Le hardware s'authentifie via device_key
def receive_sensor_data(request):
    """
    Endpoint pour recevoir les données du hardware.
    Le hardware envoie ses données avec sa device_key pour s'authentifier.
    
    Body attendu:
    {
        "device_key": "xxx",
        "cov_ppb": 400,
        "eco2_ppm": 420,
        "heart_rate": 75,
        "spo2": 98,
        "temperature": 36.8
    }
    """
    device_key = request.data.get('device_key')
    
    if not device_key:
        return Response(
            {"error": "device_key requis"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier que le device existe et est actif
    try:
        device = Device.objects.get(device_key=device_key, is_active=True)
    except Device.DoesNotExist:
        return Response(
            {"error": "Device non trouvé ou inactif"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Extraire les données du capteur
    required_fields = ['cov_ppb', 'eco2_ppm', 'heart_rate', 'spo2', 'temperature']
    sensor_values = {}
    
    for field in required_fields:
        value = request.data.get(field)
        if value is None:
            return Response(
                {"error": f"Champ requis manquant: {field}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            sensor_values[field] = float(value)
        except (ValueError, TypeError):
            return Response(
                {"error": f"Valeur invalide pour {field}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Créer l'enregistrement des données du capteur
    sensor_data = SensorData.objects.create(
        device=device,
        **sensor_values
    )
    
    # Traiter avec le modèle IA
    ai_result = predict_health_status(
        sensor_values['cov_ppb'],
        sensor_values['eco2_ppm'],
        sensor_values['heart_rate'],
        sensor_values['spo2'],
        sensor_values['temperature']
    )
    
    # Mettre à jour les données du capteur avec le résultat IA
    sensor_data.ai_status = ai_result['status']
    sensor_data.ai_status_name = ai_result['status_name']
    sensor_data.ai_confidence = ai_result['confidence']
    sensor_data.ai_probabilities = ai_result['probabilities']
    sensor_data.processed = True
    sensor_data.save()
    
    # Mettre à jour la date de dernière donnée du device
    device.last_data_at = timezone.now()
    device.save()
    
    # Créer également une entrée HealthData pour l'utilisateur
    HealthData.objects.create(
        user=device.user,
        heart_rate=sensor_values['heart_rate'],
        oxygen_level=sensor_values['spo2'],
        temperature=sensor_values['temperature'],
        respiratory_rate=int(sensor_values['eco2_ppm'] / 30),  # Estimation
        air_quality=int(sensor_values['cov_ppb'] / 10),  # Conversion en AQI approximatif
        status='normal' if ai_result['status'] == 0 else 'attention' if ai_result['status'] <= 2 else 'critical'
    )
    
    return Response({
        "success": True,
        "message": "Données reçues et traitées",
        "sensor_data_id": sensor_data.id,
        "ai_result": ai_result,
        "user": device.user.username
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_devices(request):
    """Liste les devices de l'utilisateur connecté"""
    devices = Device.objects.filter(user=request.user)
    data = [{
        "id": str(device.id),
        "name": device.name,
        "device_key": device.device_key,
        "is_active": device.is_active,
        "created_at": device.created_at.isoformat(),
        "last_data_at": device.last_data_at.isoformat() if device.last_data_at else None
    } for device in devices]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_device(request):
    """Crée un nouveau device pour l'utilisateur connecté"""
    name = request.data.get('name', 'Capteur HealthTic')
    
    # Générer une clé unique pour le device
    device_key = secrets.token_hex(32)
    
    device = Device.objects.create(
        user=request.user,
        name=name,
        device_key=device_key
    )
    
    return Response({
        "id": str(device.id),
        "name": device.name,
        "device_key": device.device_key,
        "message": "Device créé avec succès. Utilisez la device_key pour envoyer des données."
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_sensor_data(request):
    """Récupère les dernières données des capteurs de l'utilisateur"""
    devices = Device.objects.filter(user=request.user)
    
    # Récupérer les 20 dernières mesures
    sensor_data = SensorData.objects.filter(device__in=devices)[:20]
    
    data = [{
        "id": sd.id,
        "device_name": sd.device.name,
        "cov_ppb": sd.cov_ppb,
        "eco2_ppm": sd.eco2_ppm,
        "heart_rate": sd.heart_rate,
        "spo2": sd.spo2,
        "temperature": sd.temperature,
        "ai_status": sd.ai_status,
        "ai_status_name": sd.ai_status_name,
        "ai_confidence": sd.ai_confidence,
        "ai_probabilities": sd.ai_probabilities,
        "created_at": sd.created_at.isoformat()
    } for sd in sensor_data]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_ai_result(request):
    """Récupère le dernier résultat d'analyse IA pour l'utilisateur"""
    devices = Device.objects.filter(user=request.user)
    
    latest = SensorData.objects.filter(
        device__in=devices,
        processed=True
    ).first()
    
    if not latest:
        return Response({
            "message": "Aucune donnée analysée disponible"
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        "device_name": latest.device.name,
        "sensor_data": {
            "cov_ppb": latest.cov_ppb,
            "eco2_ppm": latest.eco2_ppm,
            "heart_rate": latest.heart_rate,
            "spo2": latest.spo2,
            "temperature": latest.temperature
        },
        "ai_result": {
            "status": latest.ai_status,
            "status_name": latest.ai_status_name,
            "confidence": latest.ai_confidence,
            "probabilities": latest.ai_probabilities
        },
        "analyzed_at": latest.created_at.isoformat()
    })
