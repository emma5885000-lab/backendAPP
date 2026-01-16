from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer
from django.db.models import Q, Max, Count
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageViewSet(ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.request.query_params.get('with_user', None)
        
        queryset = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )
        
        # Filtrer par conversation avec un utilisateur spécifique
        if other_user_id:
            queryset = queryset.filter(
                Q(sender_id=other_user_id) | Q(receiver_id=other_user_id)
            )
        
        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """
        Retourne la liste des conversations de l'utilisateur connecté.
        Chaque conversation contient les infos du contact et le dernier message.
        """
        user = request.user
        
        # Trouver tous les utilisateurs avec qui l'utilisateur a échangé
        sent_to = Message.objects.filter(sender=user).values_list('receiver_id', flat=True).distinct()
        received_from = Message.objects.filter(receiver=user).values_list('sender_id', flat=True).distinct()
        
        contact_ids = set(list(sent_to) + list(received_from))
        
        conversations = []
        for contact_id in contact_ids:
            contact = User.objects.get(id=contact_id)
            
            # Dernier message de cette conversation
            last_message = Message.objects.filter(
                Q(sender=user, receiver_id=contact_id) | 
                Q(sender_id=contact_id, receiver=user)
            ).order_by('-created_at').first()
            
            # Nombre de messages non lus
            unread_count = Message.objects.filter(
                sender_id=contact_id,
                receiver=user,
                is_read=False
            ).count()
            
            conversations.append({
                'contact': {
                    'id': contact.id,
                    'username': contact.username,
                    'email': contact.email,
                    'role': contact.role
                },
                'last_message': {
                    'content': last_message.content if last_message else '',
                    'created_at': last_message.created_at if last_message else None,
                    'is_from_me': last_message.sender == user if last_message else False
                },
                'unread_count': unread_count
            })
        
        # Trier par date du dernier message (les plus récents en premier)
        conversations.sort(
            key=lambda x: x['last_message']['created_at'] or '', 
            reverse=True
        )
        
        return Response(conversations)
    
    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """
        Marque tous les messages d'une conversation comme lus.
        Requiert 'contact_id' dans le body.
        """
        user = request.user
        contact_id = request.data.get('contact_id')
        
        if not contact_id:
            return Response(
                {'error': 'contact_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marquer comme lus tous les messages reçus de ce contact
        updated = Message.objects.filter(
            sender_id=contact_id,
            receiver=user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'messages_marked': updated
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Retourne le nombre total de messages non lus pour l'utilisateur.
        """
        user = request.user
        count = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})
