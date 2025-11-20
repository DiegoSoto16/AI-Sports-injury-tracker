from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status


from .models import AthleteData, InjuryPrediction,  AthleteSession
from .serializers import (
    AthleteDataSerializer,
    AthleteSessionSerializer,
    InjuryPredictionSerializer,
    PredictionHistorySerializer
)


class AthleteListView(generics.ListAPIView):
    queryset = AthleteData.objects.all()
    serializer_class = AthleteDataSerializer


class AthleteDetailView(generics.RetrieveAPIView):
    queryset = AthleteData.objects.all()
    serializer_class = AthleteDataSerializer


class InjuryPredictionListView(generics.ListAPIView):
    queryset = InjuryPrediction.objects.all()
    serializer_class = InjuryPredictionSerializer


@api_view(["POST"])
def create_prediction(request):

    # Get athlete safely — if not found, return 404
    athlete_id = request.data.get("athlete")
    athlete = get_object_or_404(AthleteData, id=athlete_id)

    # Extract relevant metrics from frontend payload
    heart_rate = float(request.data.get("heart_rate", 0))
    strain_score = float(request.data.get("strain_score", 0))
    duration = float(request.data.get("duration_minutes", 0))
    calories = float(request.data.get("calories_burned", 0))
    intensity = float(request.data.get("calculated_intensity", 0))

    # risk formula
    risk_score = round((heart_rate / 200 + strain_score + intensity) / 3, 2)
    if risk_score > 0.7:
        risk_level = "high"
    elif risk_score > 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    #  linked prediction record
    InjuryPrediction.objects.create(
        athlete=athlete,
        risk_level=risk_level,
        predicted_probability=risk_score,
        strain_score=strain_score,
    )

    return Response({
        "status": "success",
        "athlete": athlete.name,
        "risk_level": risk_level,
        "score": risk_score



    })


@api_view(["GET"])
def latest_prediction(request, athlete_id: int):
    """Return the most recent prediction for an athlete, or 404."""
    get_object_or_404(AthleteData, id=athlete_id)  # validate athlete exists
    pred = (InjuryPrediction.objects
            .filter(athlete_id=athlete_id)
            .order_by("-created_at")
            .first())
    if not pred:
        return Response({"detail": "no prediction yet"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "athlete_id": athlete_id,
        "risk_level": pred.risk_level,
        "predicted_probability": pred.predicted_probability,
        "strain_score": pred.strain_score,
        "created_at": pred.created_at,
    })


@api_view(["GET"])
def athlete_sessions(request, athlete_id: int):
    athlete = get_object_or_404(AthleteData, id=athlete_id)
    sessions = athlete.sessions.order_by("-session_date")
    serializer = AthleteSessionSerializer(sessions, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def latest_session(request, athlete_id: int):
    athlete = get_object_or_404(AthleteData, id=athlete_id)
    session = athlete.sessions.order_by("-session_date").first()
    if not session:
        return Response({"detail": "No sessions yet"}, status=404)

    serializer = AthleteSessionSerializer(session)
    return Response(serializer.data)
