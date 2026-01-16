from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from datetime import timedelta
from django.utils import timezone
from .models import HealthData
from .serializers import HealthDataSerializer

class HealthDataViewSet(ModelViewSet):
    queryset = HealthData.objects.all()
    serializer_class = HealthDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HealthData.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Endpoint pour récupérer les données du tableau de bord"""
        user = request.user
        
        # Dernière mesure
        latest = HealthData.objects.filter(user=user).first()
        
        # Historique des 7 derniers jours
        seven_days_ago = timezone.now() - timedelta(days=7)
        weekly_data = HealthData.objects.filter(
            user=user, 
            created_at__gte=seven_days_ago
        ).order_by('created_at')
        
        # Calculer les moyennes par jour pour le graphique
        trends = []
        for i in range(7):
            day = timezone.now() - timedelta(days=6-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_avg = HealthData.objects.filter(
                user=user,
                created_at__range=[day_start, day_end]
            ).aggregate(
                avg_heart=Avg('heart_rate'),
                avg_spo2=Avg('oxygen_level')
            )
            
            # Score de santé basé sur les moyennes (0-100)
            if day_avg['avg_heart'] and day_avg['avg_spo2']:
                score = min(100, int((day_avg['avg_spo2'] or 95) + (100 - abs((day_avg['avg_heart'] or 72) - 72)) / 2))
            else:
                score = 75 + i * 2  # Valeur par défaut progressive
            
            trends.append(score)
        
        # 4 dernières mesures pour l'historique
        recent_measurements = HealthData.objects.filter(user=user)[:4]
        history = []
        for m in recent_measurements:
            history.append({
                'date': m.created_at.strftime('%d %b %H:%M'),
                'status': m.get_status_display_fr(),
                'color': '#10b981' if m.status == 'normal' else '#f59e0b' if m.status == 'attention' else '#ef4444'
            })
        
        # Données actuelles (0 si aucune donnée n'existe)
        current_stats = {
            'respiratory_rate': latest.respiratory_rate if latest else 0,
            'heart_rate': latest.heart_rate if latest else 0,
            'spo2': latest.oxygen_level if latest else 0,
            'air_quality': latest.air_quality if latest else 0,
            'temperature': latest.temperature if latest else 0,
        }
        
        # Statuts des mesures
        def get_status(value, type):
            if type == 'spo2':
                return 'Excellente' if value >= 95 else 'Normale' if value >= 90 else 'Attention'
            elif type == 'heart_rate':
                return 'Normale' if 60 <= value <= 100 else 'Attention'
            elif type == 'respiratory_rate':
                return 'Normale' if 12 <= value <= 20 else 'Attention'
            elif type == 'air_quality':
                return 'Bonne' if value <= 50 else 'Modérée' if value <= 100 else 'Mauvaise'
            return 'Normale'
        
        stats_with_status = {
            'respiratory_rate': {
                'value': current_stats['respiratory_rate'],
                'unit': '/min',
                'status': get_status(current_stats['respiratory_rate'], 'respiratory_rate'),
                'color': '#10b981'
            },
            'heart_rate': {
                'value': current_stats['heart_rate'],
                'unit': ' bpm',
                'status': get_status(current_stats['heart_rate'], 'heart_rate'),
                'color': '#3b82f6'
            },
            'spo2': {
                'value': current_stats['spo2'],
                'unit': '%',
                'status': get_status(current_stats['spo2'], 'spo2'),
                'color': '#8b5cf6'
            },
            'air_quality': {
                'value': current_stats['air_quality'],
                'unit': ' AQI',
                'status': get_status(current_stats['air_quality'], 'air_quality'),
                'color': '#f59e0b'
            },
            'temperature': {
                'value': current_stats['temperature'],
                'unit': '°C',
                'status': 'Normale' if 36.1 <= current_stats['temperature'] <= 37.2 else 'Attention',
                'color': '#f59e0b'
            }
        }
        
        return Response({
            'stats': stats_with_status,
            'trends': trends,
            'history': history,
            'recent_measurements': [
                {
                    'label': 'Fréquence respiratoire',
                    'value': f"{current_stats['respiratory_rate']} /min",
                    'color': '#10b981'
                },
                {
                    'label': 'SpO2',
                    'value': f"{current_stats['spo2']}%",
                    'color': '#8b5cf6'
                },
                {
                    'label': 'Fréquence cardiaque',
                    'value': f"{current_stats['heart_rate']} bpm",
                    'color': '#3b82f6'
                },
                {
                    'label': 'Température',
                    'value': f"{current_stats['temperature']}°C",
                    'color': '#f59e0b'
                }
            ]
        })

    @action(detail=False, methods=['get'])
    def prediction(self, request):
        """Endpoint pour les prédictions IA basées sur les données de santé de l'utilisateur"""
        user = request.user
        
        # Récupérer les données de santé de l'utilisateur
        latest = HealthData.objects.filter(user=user).first()
        all_data = HealthData.objects.filter(user=user)
        data_count = all_data.count()
        
        # Calculer les moyennes si des données existent
        if data_count > 0:
            averages = all_data.aggregate(
                avg_heart=Avg('heart_rate'),
                avg_spo2=Avg('oxygen_level'),
                avg_temp=Avg('temperature'),
                avg_respiratory=Avg('respiratory_rate'),
                avg_air=Avg('air_quality')
            )
            
            # Calculer le score de santé (0-10)
            spo2_score = min(10, (averages['avg_spo2'] or 0) / 10) if averages['avg_spo2'] else 0
            heart_score = 10 - min(10, abs((averages['avg_heart'] or 72) - 72) / 5) if averages['avg_heart'] else 0
            temp_score = 10 - min(10, abs((averages['avg_temp'] or 37) - 37) * 2) if averages['avg_temp'] else 0
            health_score = round((spo2_score + heart_score + temp_score) / 3, 1)
            
            # Calculer le risque relatif (0-100%)
            risk_factors = 0
            if averages['avg_spo2'] and averages['avg_spo2'] < 95:
                risk_factors += 20
            if averages['avg_heart'] and (averages['avg_heart'] < 60 or averages['avg_heart'] > 100):
                risk_factors += 15
            if averages['avg_temp'] and (averages['avg_temp'] < 36 or averages['avg_temp'] > 37.5):
                risk_factors += 15
            if averages['avg_air'] and averages['avg_air'] > 50:
                risk_factors += 10
            if averages['avg_respiratory'] and (averages['avg_respiratory'] < 12 or averages['avg_respiratory'] > 20):
                risk_factors += 10
            
            relative_risk = min(100, risk_factors)
            
            # Confiance IA basée sur le nombre de données
            confidence = min(95, 50 + data_count * 5)
            
            # Déterminer le niveau de risque
            if relative_risk < 20:
                risk_level = 'Faible'
                risk_color = 'emerald'
            elif relative_risk < 50:
                risk_level = 'Modéré'
                risk_color = 'amber'
            else:
                risk_level = 'Élevé'
                risk_color = 'red'
            
            # Facteurs de risque identifiés
            risk_factors_list = []
            if averages['avg_air'] and averages['avg_air'] > 50:
                risk_factors_list.append("Exposition prolongée à la pollution atmosphérique")
            if averages['avg_spo2'] and averages['avg_spo2'] < 95:
                risk_factors_list.append("Niveau d'oxygène sanguin bas")
            if averages['avg_heart'] and averages['avg_heart'] > 100:
                risk_factors_list.append("Fréquence cardiaque élevée")
            if averages['avg_temp'] and averages['avg_temp'] > 37.5:
                risk_factors_list.append("Température corporelle élevée")
            if averages['avg_respiratory'] and averages['avg_respiratory'] > 20:
                risk_factors_list.append("Fréquence respiratoire élevée")
            
            # Recommandations personnalisées
            recommendations = []
            if averages['avg_spo2'] and averages['avg_spo2'] < 95:
                recommendations.append({
                    'icon': '🫁',
                    'title': 'Exercices respiratoires',
                    'description': 'Pratiquez des exercices de respiration profonde pour améliorer votre oxygénation',
                    'bgClass': 'bg-blue-100'
                })
            if averages['avg_heart'] and averages['avg_heart'] > 100:
                recommendations.append({
                    'icon': '🧘',
                    'title': 'Relaxation',
                    'description': 'Pratiquez des techniques de relaxation pour réduire votre fréquence cardiaque',
                    'bgClass': 'bg-purple-100'
                })
            if averages['avg_air'] and averages['avg_air'] > 50:
                recommendations.append({
                    'icon': '🌬️',
                    'title': "Qualité de l'air",
                    'description': "Évitez les sorties lors des pics de pollution et aérez votre intérieur",
                    'bgClass': 'bg-teal-100'
                })
            
            # Ajouter des recommandations générales si la liste est vide
            if len(recommendations) == 0:
                recommendations = [
                    {
                        'icon': '💪',
                        'title': 'Activité physique',
                        'description': 'Maintenir une activité physique régulière de 30 minutes par jour',
                        'bgClass': 'bg-blue-100'
                    },
                    {
                        'icon': '🥗',
                        'title': 'Alimentation équilibrée',
                        'description': 'Adoptez une alimentation riche en fruits et légumes',
                        'bgClass': 'bg-green-100'
                    }
                ]
            
            # Ajouter la recommandation de suivi médical
            recommendations.append({
                'icon': '📅',
                'title': 'Suivi médical',
                'description': 'Consultation de suivi recommandée pour un bilan complet',
                'bgClass': 'bg-amber-100'
            })
            
        else:
            # Aucune donnée disponible - renvoyer des valeurs à 0
            health_score = 0
            relative_risk = 0
            confidence = 0
            risk_level = 'Inconnu'
            risk_color = 'gray'
            risk_factors_list = []
            recommendations = []
        
        return Response({
            'health_score': health_score,
            'relative_risk': relative_risk,
            'confidence': confidence,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': risk_factors_list,
            'recommendations': recommendations,
            'data_count': data_count
        })
