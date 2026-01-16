from rest_framework import serializers
from .models import HealthData

class HealthDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = '__all__'
        read_only_fields = ['user']
