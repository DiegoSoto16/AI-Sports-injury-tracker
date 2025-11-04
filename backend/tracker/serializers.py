from rest_framework import serializers
from .models import Athlete, InjuryPrediction


class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Athlete
        fields = '__all__'


class InjuryPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InjuryPrediction
        fields = '__all__'
