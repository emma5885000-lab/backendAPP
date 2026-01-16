# alerts/utils.py
from .models import Alert

def check_vital_signs(user, spo2, heart_rate, tcov, temp):
    """
    Génère des alertes automatiques en fonction de SpO2, fréquence cardiaque, Tcov et température
    """
    alerts = []

    # SpO2
    if spo2 < 90:
        alerts.append(Alert(
            user=user,
            title="SpO₂ critique",
            message=f"Votre saturation en oxygène est très basse ({spo2}%) !",
            level="danger"
        ))
    elif spo2 < 95:
        alerts.append(Alert(
            user=user,
            title="SpO₂ faible",
            message=f"Votre saturation en oxygène est légèrement basse ({spo2}%).",
            level="warning"
        ))

    # Fréquence cardiaque
    if heart_rate > 120:
        alerts.append(Alert(
            user=user,
            title="Fréquence cardiaque élevée",
            message=f"Votre rythme cardiaque est de {heart_rate} bpm !",
            level="danger"
        ))
    elif heart_rate > 100:
        alerts.append(Alert(
            user=user,
            title="Fréquence cardiaque un peu élevée",
            message=f"Votre rythme cardiaque est de {heart_rate} bpm.",
            level="warning"
        ))

    # Tcov
    if tcov > 38:
        alerts.append(Alert(
            user=user,
            title="Tcov élevée",
            message=f"Votre Tcov est de {tcov}°C, risque potentiel de COVID.",
            level="danger"
        ))
    elif tcov > 37:
        alerts.append(Alert(
            user=user,
            title="Tcov légèrement élevée",
            message=f"Votre Tcov est de {tcov}°C.",
            level="warning"
        ))

    # Température
    if temp > 38.5:
        alerts.append(Alert(
            user=user,
            title="Fièvre élevée",
            message=f"Votre température est de {temp}°C !",
            level="danger"
        ))
    elif temp > 37.5:
        alerts.append(Alert(
            user=user,
            title="Fièvre légère",
            message=f"Votre température est de {temp}°C.",
            level="warning"
        ))

    # Sauvegarder toutes les alertes générées
    for alert in alerts:
        alert.save()
