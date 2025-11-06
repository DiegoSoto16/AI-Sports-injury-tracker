from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import AthleteData, InjuryPrediction, PredictionHistory
from .serializers import AthleteDataSerializer, InjuryPredictionSerializer, PredictionHistorySerializer
from .ml_model import predict_injury_risk


@api_view(["GET"])
def get_all_athletes(request):
    athletes = AthleteData.objects.all()
    serializer = AthleteDataSerializer(athletes, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_all_predictions(request):
    predictions = InjuryPrediction.objects.all().order_by("-created_at")
    serializer = InjuryPredictionSerializer(predictions, many=True)
    return Response(serializer.data)

# Predict New Injury Risk


@api_view(["POST"])
def predict_view(request):
    """
    Accepts athlete data, calculates injury risk,
    and saves both the InjuryPrediction and PredictionHistory.
    """
    data = request.data
    try:
        heart_rate = float(data.get("heart_rate"))
        duration = float(data.get("duration_minutes"))
        calories = float(data.get("calories_burned"))
        calculated_intensity = float(data.get("calculated_intensity", 0.5))
        strain_score = float(data.get("strain_score", 0.5))

        risk_score = predict_injury_risk(
            heart_rate, duration, calories, calculated_intensity, strain_score)

        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        prediction = InjuryPrediction.objects.create(
            athlete=AthleteData.objects.first(),  # or dynamically linked athlete
            risk_level=risk_level,
            predicted_probability=risk_score,
            strain_score=strain_score,
        )

        PredictionHistory.objects.create(
            name=data.get("name", "Unknown"),
            sport=data.get("sport", "Unknown"),
            team=data.get("team", "Unknown"),
            heart_rate=heart_rate,
            duration_minutes=duration,
            calories_burned=calories,
            experience_years=data.get("experience_years", 0),
            calculated_intensity=calculated_intensity,
            risk_level=risk_level,
            strain_score=strain_score,
        )

        serializer = InjuryPredictionSerializer(prediction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
