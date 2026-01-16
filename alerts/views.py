# alerts/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Alert
from .serializers import AlertSerializer

class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les alertes.
    - GET /api/alerts/          -> lister les alertes de l'utilisateur connecté
    - POST /api/alerts/         -> créer une alerte
    - PUT/PATCH /api/alerts/{id}/ -> modifier une alerte
    - DELETE /api/alerts/{id}/  -> supprimer une alerte
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retourne uniquement les alertes de l'utilisateur connecté"""
        return Alert.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Associe l'alerte à l'utilisateur connecté lors de la création"""
        serializer.save(user=self.request.user)
