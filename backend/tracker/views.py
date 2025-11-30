from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from .models import AthleteSession, AthleteData
from django.db.models import Avg
from datetime import timedelta
from django.utils import timezone
from typing import Dict


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

# ----------------- WORKLOAD & FATIGUE FEATURES ----------------- #


SLEEP_TARGET_HOURS = 7.5  # Option B: your chosen target


def compute_workload_features(athlete) -> Dict[str, float]:
    """
    Compute acute load, chronic load, ACWR, and sleep debt
    using the athlete's recent sessions.
    """
    now = timezone.now()
    today = now.date()

    # Last 14 days for chronic load
    last_14 = athlete.sessions.filter(
        session_date__date__gte=today - timedelta(days=14)
    ).order_by("session_date")

    # Last 7 days for acute load
    last_7 = athlete.sessions.filter(
        session_date__date__gte=today - timedelta(days=7)
    ).order_by("session_date")

    # If we somehow have no sessions, fall back to neutral defaults
    if not last_14.exists():
        return {
            "acute_load": 0.0,
            "chronic_load": 0.0,
            "acwr": 1.0,         # neutral
            "sleep_debt": 0.0,
        }

    # For this prototype, treat strain_score as "session load"
    acute_load = 0.0
    if last_7.exists():
        acute_load = sum(s.strain_score for s in last_7) / last_7.count()

    chronic_load = sum(s.strain_score for s in last_14) / last_14.count()

    if chronic_load > 0:
        acwr = acute_load / chronic_load
    else:
        acwr = 1.0  # neutral if we can't compute it

    # Sleep debt over the last 7 days
    if last_7.exists():
        avg_sleep = sum(s.sleep_hours for s in last_7) / last_7.count()
        sleep_debt = max(0.0, SLEEP_TARGET_HOURS - avg_sleep)
    else:
        sleep_debt = 0.0

    return {
        "acute_load": round(acute_load, 2),
        "chronic_load": round(chronic_load, 2),
        "acwr": round(acwr, 2),
        "sleep_debt": round(sleep_debt, 2),
    }


def acwr_risk_component(acwr: float) -> float:
    """
    Turn ACWR into a risk number between 0 and 1.

    Safe-ish zone: 0.8–1.3
    High risk when you spike above ~1.5 or drop way below 0.8.
    """
    if acwr <= 0:
        return 0.5
    if acwr < 0.8:
        return 0.4           # under-prepared
    elif acwr <= 1.3:
        return 0.1           # "sweet spot"
    elif acwr <= 1.5:
        return 0.4
    elif acwr <= 2.0:
        return 0.7
    else:
        return 0.9           # big spike = very risky


def sleep_risk_component(sleep_debt: float) -> float:
    """
    0 hours debt → 0 risk
    3+ hours debt → capped at 1.0
    """
    return max(0.0, min(sleep_debt / 3.0, 1.0))


def strain_risk_component(strain_score: float) -> float:
    """
    Strain is roughly 0–10 in your data. Normalize to 0–1.
    """
    return max(0.0, min(strain_score / 10.0, 1.0))
# -----------


@api_view(["POST"])
def create_prediction(request):
    from .ml_predictor import predict_injury

    athlete_id = request.data.get("athlete")
    athlete = get_object_or_404(AthleteData, id=athlete_id)

    # ---- Metrics from frontend (latest session) ---- #
    heart_rate = float(request.data.get("heart_rate", 0))
    sleep_hours = float(request.data.get("sleep_hours", 0))
    steps = int(request.data.get("steps", 0))
    calories_burned = float(request.data.get("calories_burned", 0))
    intensity = float(request.data.get("calculated_intensity", 0))
    strain_score = float(request.data.get("strain_score", 0))
    fatigue_level = int(request.data.get("fatigue_level", 0))

    # ---- 1) TensorFlow model probability ---- #
    model_prob = predict_injury(
        heart_rate,
        sleep_hours,
        steps,
        calories_burned,
        intensity,
        strain_score,
    )  # returns 0.0–1.0

    # ---- 2) Workload & sleep context (ACWR + sleep debt) ---- #
    workload = compute_workload_features(athlete)
    acwr = workload["acwr"]
    sleep_debt = workload["sleep_debt"]

    acwr_risk = acwr_risk_component(acwr)
    sleep_risk = sleep_risk_component(sleep_debt)
    strain_risk = strain_risk_component(strain_score)

    # Context risk mixes ACWR + strain + sleep debt
    context_risk = (
        0.5 * acwr_risk +
        0.3 * strain_risk +
        0.2 * sleep_risk
    )

    # ---- 3) Final hybrid risk ---- #
    # 60% ML model + 40% context (ACWR + sleep + strain)
    hybrid_risk = 0.6 * float(model_prob) + 0.4 * float(context_risk)
    hybrid_risk = max(0.0, min(hybrid_risk, 1.0))

    # Convert to risk category
    if hybrid_risk > 0.7:
        risk_level = "high"
    elif hybrid_risk > 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    # ---- 4) Save prediction record (used by /predictions/latest/) ---- #
    InjuryPrediction.objects.create(
        athlete=athlete,
        risk_level=risk_level,
        predicted_probability=hybrid_risk,
        strain_score=strain_score,
    )

    # ---- 5) Return detailed response to frontend ---- #
    return Response({
        "status": "success",
        "athlete": athlete.name,
        # main value the frontend uses:
        "probability": hybrid_risk,
        "risk_level": risk_level,
        # extra transparency for your explanation/demo:
        "details": {
            "model_probability": model_prob,
            "context_risk": round(context_risk, 3),
            "acwr": acwr,
            "acute_load": workload["acute_load"],
            "chronic_load": workload["chronic_load"],
            "sleep_debt": sleep_debt,
            "sleep_target": SLEEP_TARGET_HOURS,
            "strain_score": strain_score,
            "fatigue_level": fatigue_level,
        },
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
def latest_session(request, athlete_id):
    try:
        athlete = AthleteData.objects.get(id=athlete_id)

        latest = athlete.sessions.order_by("-session_date").first()

        if not latest:
            return Response({"error": "No session data found"}, status=404)

        return Response({
            "id": athlete.id,
            "name": athlete.name,
            "age": athlete.age,
            "sport": athlete.sport,
            "team": athlete.team,
            "experience_years": athlete.experience_years,

            # RETURN LATEST SESSION METRICS
            "heart_rate": latest.heart_rate,
            "sleep_hours": latest.sleep_hours,
            "steps": latest.steps,
            "calories_burned": latest.calories_burned,
            "strain_score": latest.strain_score,
            "intensity": latest.calculated_intensity,
            "fatigue_level": latest.fatigue_level,

            # PROFILE AVERAGES
            "avg_heart_rate": athlete.avg_heart_rate,
            "avg_sleep_hours": athlete.avg_sleep_hours,
            "avg_steps": athlete.avg_steps,
            "avg_calories_burned": athlete.avg_calories_burned,
            "avg_intensity": athlete.avg_intensity,
            "avg_strain": athlete.avg_strain,
        }, status=200)

    except AthleteData.DoesNotExist:
        return Response({"error": "Athlete not found"}, status=404)


@api_view(["GET"])
def athlete_history(request, pk):
    try:
        athlete = AthleteData.objects.get(id=pk)
        sessions = athlete.sessions.order_by("session_date")

        return Response([
            {
                "date": s.session_date.date(),
                "heart_rate": s.heart_rate,
                "sleep_hours": s.sleep_hours,
                "steps": s.steps,
                "calories_burned": s.calories_burned,
                "strain_score": s.strain_score,
                "intensity": s.calculated_intensity,
            }
            for s in sessions
        ])
    except AthleteData.DoesNotExist:
        return Response({"error": "Athlete not found"}, status=404)
