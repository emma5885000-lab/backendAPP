from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from alerts.utils import check_vital_signs

User = get_user_model()  # prend ton User personnalisé

class MeasurementAPIView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            spo2 = float(request.data.get('spo2'))
            heart_rate = int(request.data.get('heart_rate'))
            tcov = float(request.data.get('tcov'))
            temp = float(request.data.get('temp'))

            user = User.objects.get(id=user_id)

            check_vital_signs(user, spo2, heart_rate, tcov, temp)

            return Response({"message": "Mesures reçues et alertes générées"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
