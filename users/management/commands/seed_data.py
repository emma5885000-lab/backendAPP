"""
Commande Django pour générer des données de test.
Exécuter avec: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from devices.models import Device, SensorData
from health.models import HealthData
from alerts.models import Alert
from chat.models import Message
from rest_framework.authtoken.models import Token
import random
import secrets
from datetime import timedelta


class Command(BaseCommand):
    help = 'Génère des données de test pour l\'application HealthTic'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SEEDING DE LA BASE DE DONNÉES HEALTHTIC")
        self.stdout.write("=" * 60)

        # 1. CRÉATION DES MÉDECINS
        self.stdout.write("\n[1/6] Création des médecins...")
        medecins_data = [
            {"username": "dr_martin", "email": "dr.martin@healthtic.com", "password": "medecin123", "first_name": "Jean", "last_name": "Martin"},
            {"username": "dr_dubois", "email": "dr.dubois@healthtic.com", "password": "medecin123", "first_name": "Marie", "last_name": "Dubois"},
        ]

        medecins = []
        for data in medecins_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "role": "doctor",
                    "first_name": data["first_name"],
                    "last_name": data["last_name"]
                }
            )
            if created:
                user.set_password(data["password"])
                user.save()
                Token.objects.get_or_create(user=user)
                self.stdout.write(f"  ✓ Médecin créé: {user.username}")
            else:
                self.stdout.write(f"  - Médecin existant: {user.username}")
            medecins.append(user)

        # 2. CRÉATION DES PATIENTS
        self.stdout.write("\n[2/6] Création des patients...")
        patients_data = [
            {"username": "patient_alice", "email": "alice@example.com", "password": "patient123", "first_name": "Alice", "last_name": "Dupont"},
            {"username": "patient_bob", "email": "bob@example.com", "password": "patient123", "first_name": "Bob", "last_name": "Leroy"},
            {"username": "patient_claire", "email": "claire@example.com", "password": "patient123", "first_name": "Claire", "last_name": "Bernard"},
            {"username": "patient_david", "email": "david@example.com", "password": "patient123", "first_name": "David", "last_name": "Moreau"},
            {"username": "patient_emma", "email": "emma@example.com", "password": "patient123", "first_name": "Emma", "last_name": "Petit"},
        ]

        patients = []
        for i, data in enumerate(patients_data):
            medecin_assigne = medecins[i % len(medecins)]
            
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "role": "patient",
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "medecin": medecin_assigne
                }
            )
            if created:
                user.set_password(data["password"])
                user.save()
                Token.objects.get_or_create(user=user)
                self.stdout.write(f"  ✓ Patient créé: {user.username} → Médecin: {medecin_assigne.username}")
            else:
                if not user.medecin:
                    user.medecin = medecin_assigne
                    user.save()
                self.stdout.write(f"  - Patient existant: {user.username}")
            patients.append(user)

        # 3. CRÉATION DES DEVICES
        self.stdout.write("\n[3/6] Création des devices...")
        devices = []
        for patient in patients:
            device, created = Device.objects.get_or_create(
                user=patient,
                defaults={
                    "name": f"Capteur de {patient.first_name}",
                    "device_key": secrets.token_hex(32),
                    "is_active": True
                }
            )
            if created:
                self.stdout.write(f"  ✓ Device créé: {device.name}")
            else:
                self.stdout.write(f"  - Device existant: {device.name}")
            devices.append(device)

        # 4. CRÉATION DES DONNÉES DE CAPTEURS
        self.stdout.write("\n[4/6] Création des données de capteurs...")
        ai_statuses = [(0, "Sain"), (1, "Infection légère"), (2, "Infection modérée"), (3, "Hypoxie sévère")]

        for device in devices:
            existing_count = SensorData.objects.filter(device=device).count()
            if existing_count >= 10:
                self.stdout.write(f"  - Données existantes pour {device.user.username}")
                continue
                
            for j in range(10):
                is_healthy = random.random() > 0.3
                
                if is_healthy:
                    cov_ppb = random.uniform(100, 300)
                    eco2_ppm = random.uniform(400, 600)
                    heart_rate = random.uniform(60, 90)
                    spo2 = random.uniform(96, 100)
                    temperature = random.uniform(36.2, 37.2)
                    ai_status = 0
                else:
                    cov_ppb = random.uniform(300, 800)
                    eco2_ppm = random.uniform(600, 1200)
                    heart_rate = random.uniform(85, 120)
                    spo2 = random.uniform(88, 96)
                    temperature = random.uniform(37.5, 39.5)
                    ai_status = random.choice([1, 2, 3])
                
                created_at = timezone.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
                
                sensor_data = SensorData.objects.create(
                    device=device,
                    cov_ppb=round(cov_ppb, 2),
                    eco2_ppm=round(eco2_ppm, 2),
                    heart_rate=round(heart_rate, 1),
                    spo2=round(spo2, 1),
                    temperature=round(temperature, 1),
                    ai_status=ai_status,
                    ai_status_name=ai_statuses[ai_status][1],
                    ai_confidence=round(random.uniform(0.75, 0.99), 2),
                    ai_probabilities={
                        "Sain": round(random.uniform(0.1, 0.9), 2),
                        "Infection légère": round(random.uniform(0.05, 0.3), 2),
                        "Infection modérée": round(random.uniform(0.02, 0.2), 2),
                        "Hypoxie sévère": round(random.uniform(0.01, 0.1), 2)
                    },
                    processed=True
                )
                sensor_data.created_at = created_at
                sensor_data.save(update_fields=['created_at'])
                
                status_health = 'normal' if ai_status == 0 else 'attention' if ai_status <= 2 else 'danger'
                health_data = HealthData.objects.create(
                    user=device.user,
                    heart_rate=int(heart_rate),
                    oxygen_level=round(spo2, 1),
                    temperature=round(temperature, 1),
                    respiratory_rate=int(eco2_ppm / 30),
                    air_quality=int(cov_ppb / 10),
                    status=status_health
                )
                health_data.created_at = created_at
                health_data.save(update_fields=['created_at'])
            
            device.last_data_at = timezone.now()
            device.save()
            self.stdout.write(f"  ✓ 10 mesures créées pour {device.user.username}")

        # 5. CRÉATION DES ALERTES
        self.stdout.write("\n[5/6] Création des alertes...")
        alertes_templates = [
            {"title": "Fréquence cardiaque élevée", "message": "Votre fréquence cardiaque a dépassé 100 bpm.", "level": "warning"},
            {"title": "SpO2 bas détecté", "message": "Votre niveau d'oxygène est inférieur à 95%.", "level": "danger"},
            {"title": "Température élevée", "message": "Votre température corporelle est de 38.5°C.", "level": "warning"},
            {"title": "Qualité de l'air dégradée", "message": "La qualité de l'air est mauvaise.", "level": "info"},
            {"title": "Rappel de mesure", "message": "N'oubliez pas vos mesures quotidiennes.", "level": "info"},
        ]

        for patient in patients:
            existing_alerts = Alert.objects.filter(user=patient).count()
            if existing_alerts >= 2:
                self.stdout.write(f"  - Alertes existantes pour {patient.username}")
                continue
                
            num_alertes = random.randint(2, 4)
            for _ in range(num_alertes):
                template = random.choice(alertes_templates)
                Alert.objects.create(
                    user=patient,
                    title=template["title"],
                    message=template["message"],
                    level=template["level"],
                    is_read=random.choice([True, False])
                )
            self.stdout.write(f"  ✓ {num_alertes} alertes créées pour {patient.username}")

        # 6. CRÉATION DES MESSAGES
        self.stdout.write("\n[6/6] Création des messages...")
        messages_templates = [
            "Bonjour, comment allez-vous aujourd'hui ?",
            "J'ai remarqué que vos dernières mesures sont un peu élevées.",
            "N'oubliez pas de prendre vos médicaments.",
            "Merci docteur, je me sens mieux aujourd'hui.",
            "J'ai quelques questions concernant mes résultats.",
            "Vos résultats sont bons, continuez ainsi !",
        ]

        for patient in patients:
            if patient.medecin:
                existing_msgs = Message.objects.filter(sender=patient.medecin, receiver=patient).count()
                if existing_msgs >= 2:
                    self.stdout.write(f"  - Messages existants pour {patient.username}")
                    continue
                    
                for _ in range(random.randint(2, 4)):
                    msg = Message.objects.create(
                        sender=patient.medecin,
                        receiver=patient,
                        content=random.choice(messages_templates),
                        is_read=random.choice([True, False])
                    )
                    msg.created_at = timezone.now() - timedelta(days=random.randint(0, 5))
                    msg.save(update_fields=['created_at'])
                
                for _ in range(random.randint(1, 3)):
                    msg = Message.objects.create(
                        sender=patient,
                        receiver=patient.medecin,
                        content=random.choice(messages_templates),
                        is_read=random.choice([True, False])
                    )
                    msg.created_at = timezone.now() - timedelta(days=random.randint(0, 5))
                    msg.save(update_fields=['created_at'])
                
                self.stdout.write(f"  ✓ Messages créés pour {patient.username}")

        # RÉSUMÉ
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SEEDING TERMINÉ AVEC SUCCÈS!"))
        self.stdout.write("=" * 60)
        
        self.stdout.write("\nCOMPTES DE TEST:")
        self.stdout.write("-" * 40)
        self.stdout.write("\nMÉDECINS:")
        for m in medecins:
            self.stdout.write(f"   Email: {m.email} | Mot de passe: medecin123")
        
        self.stdout.write("\nPATIENTS:")
        for p in patients:
            self.stdout.write(f"   Email: {p.email} | Mot de passe: patient123")
        
        self.stdout.write(f"\nSTATISTIQUES:")
        self.stdout.write(f"   - {User.objects.filter(role='doctor').count()} médecins")
        self.stdout.write(f"   - {User.objects.filter(role='patient').count()} patients")
        self.stdout.write(f"   - {Device.objects.count()} devices")
        self.stdout.write(f"   - {SensorData.objects.count()} données de capteurs")
        self.stdout.write(f"   - {HealthData.objects.count()} données de santé")
        self.stdout.write(f"   - {Alert.objects.count()} alertes")
        self.stdout.write(f"   - {Message.objects.count()} messages")
