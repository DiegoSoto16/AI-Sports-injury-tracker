from rest_framework import serializers
from .models import AthleteData, InjuryPrediction, PredictionHistory, AthleteSession


class AthleteSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteSession
        fields = "__all__"


class AthleteDataSerializer(serializers.ModelSerializer):

    #  Disable reverse FK field
    sessions = None

    # Averages we computed in the view
    avg_heart_rate = serializers.FloatField(read_only=True)
    avg_sleep_hours = serializers.FloatField(read_only=True)
    avg_steps = serializers.FloatField(read_only=True)
    avg_calories_burned = serializers.FloatField(read_only=True)
    avg_intensity = serializers.FloatField(read_only=True)
    avg_strain = serializers.FloatField(read_only=True)

    class Meta:
        model = AthleteData
        fields = [
            "id",
            "name",
            "age",
            "sport",
            "team",
            "experience_years",

            # Average session metrics
            "avg_heart_rate",
            "avg_sleep_hours",
            "avg_steps",
            "avg_calories_burned",
            "avg_intensity",
            "avg_strain",
        ]


# Injury Prediction Serializer


class InjuryPredictionSerializer(serializers.ModelSerializer):
    athlete_name = serializers.CharField(source="athlete.name", read_only=True)
    sport = serializers.CharField(source="athlete.sport", read_only=True)
    team = serializers.CharField(source="athlete.team", read_only=True)
    heart_rate = serializers.FloatField(
        source="athlete.heart_rate", read_only=True)
    duration_minutes = serializers.FloatField(
        source="athlete.duration_minutes", read_only=True)
    calories_burned = serializers.FloatField(
        source="athlete.calories_burned", read_only=True)
    experience_years = serializers.FloatField(
        source="athlete.experience_years", read_only=True)
    calculated_intensity = serializers.FloatField(
        source="athlete.calculated_intensity", read_only=True)

    class Meta:
        model = InjuryPrediction
        fields = [
            "athlete_name",
            "sport",
            "team",
            "heart_rate",
            "duration_minutes",
            "calories_burned",
            "experience_years",
            "calculated_intensity",
            "risk_level",
            "strain_score",
            "created_at",
        ]

# Prediction History Serializer


class PredictionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionHistory
        fields = "__all__"


class SimplePredictionInputSerializer(serializers.Serializer):
    heart_rate = serializers.FloatField()
    calories_burned = serializers.FloatField()
    fatigue_level = serializers.FloatField(required=False)
    sleep_hours = serializers.FloatField(required=False)
    steps = serializers.IntegerField(required=False)
