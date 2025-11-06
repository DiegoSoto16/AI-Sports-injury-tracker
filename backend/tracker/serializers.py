from rest_framework import serializers
from .models import AthleteData, InjuryPrediction


class AthleteDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteData
        fields = '__all__'
        read_only_fields = ('heart_rate', 'calories_burned',
                            'duration_minutes', 'calculated_intensity')


class InjuryPredictionSerializer(serializers.ModelSerializer):
    athlete = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = InjuryPrediction
        fields = ['id', 'risk_level', 'predicted_probability',
                  'strain_score', 'athlete', 'created_at']
