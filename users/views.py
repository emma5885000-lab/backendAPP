from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from rest_framework.decorators import api_view
from .serializers import RegisterSerializer, LoginSerializer
from .models import User

# Inscription
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                },
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Connexion
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                },
                "token": token.key
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Liste de tous les docteurs
@api_view(['GET'])
def doctor_list(request):
    doctors = User.objects.filter(role='doctor')
    data = [
        {
            "id": doc.id,
            "username": doc.username,
            "email": doc.email,
            "role": doc.role
        } for doc in doctors
    ]
    return Response(data, status=status.HTTP_200_OK)

# Liste de tous les patients
@api_view(['GET'])
def patient_list(request):
    patients = User.objects.filter(role='patient')
    data = [
        {
            "id": patient.id,
            "username": patient.username,
            "email": patient.email,
            "role": patient.role
        } for patient in patients
    ]
    return Response(data, status=status.HTTP_200_OK)

# Retourne les contacts disponibles en fonction du rôle de l'utilisateur
@api_view(['GET'])
def contacts_list(request):
    """
    Retourne la liste des contacts disponibles pour l'utilisateur connecté.
    - Si l'utilisateur est un patient, retourne son médecin assigné (ou tous les docteurs si non assigné)
    - Si l'utilisateur est un docteur, retourne ses patients assignés
    """
    user = request.user
    
    if not user.is_authenticated:
        return Response({"error": "Authentification requise"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.role == 'patient':
        # Si le patient a un médecin assigné, retourner uniquement ce médecin
        if user.medecin:
            contacts = [user.medecin]
        else:
            # Sinon, retourner tous les docteurs disponibles
            contacts = User.objects.filter(role='doctor')
    else:
        # Les docteurs voient leurs patients assignés
        contacts = user.patients.all()
        if not contacts.exists():
            # Si pas de patients assignés, montrer tous les patients
            contacts = User.objects.filter(role='patient')
    
    data = [
        {
            "id": contact.id,
            "username": contact.username,
            "email": contact.email,
            "role": contact.role,
            "is_assigned": user.role == 'patient' and user.medecin_id == contact.id if user.role == 'patient' else contact.medecin_id == user.id
        } for contact in contacts
    ]
    return Response(data, status=status.HTTP_200_OK)
