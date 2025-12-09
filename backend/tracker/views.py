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

    return max(0.0, min(strain_score / 10.0, 1.0))
# -----------


@api_view(["POST"])
def create_prediction(request):

    from .ml_predictor import predict_injury

    # -------- 1) GET ATHLETE --------
    athlete_id = request.data.get("athlete")
    athlete = get_object_or_404(AthleteData, id=athlete_id)

    # -------- 2) EXTRACT INPUT FEATURES --------
    heart_rate = float(request.data.get("heart_rate", 0))
    sleep_hours = float(request.data.get("sleep_hours", 0))
    steps = int(request.data.get("steps", 0))
    calories_burned = float(request.data.get("calories_burned", 0))
    intensity = float(request.data.get("calculated_intensity", 0))
    strain_score = float(request.data.get("strain_score", 0))

    # -------- 3) BASE ML PREDICTION --------
    ml_probability = float(
        predict_injury(
            heart_rate,
            sleep_hours,
            steps,
            calories_burned,
            intensity,
            strain_score,
        )
    )

    # -------- 4) WORKLOAD RISK LAYER (ACWR) --------
    # ACWR already computed & stored on athlete model
    try:
        acwr = float(athlete.acwr) if athlete.acwr is not None else None
    except:
        acwr = None  # NaN-safe

    if acwr is None:
        acwr_component = None
    elif acwr <= 0.8:
        acwr_component = 0.2  # under-prepared
    elif acwr <= 1.3:
        acwr_component = 0.4  # sweet spot
    elif acwr <= 1.6:
        acwr_component = 0.7  # elevated strain
    else:
        acwr_component = 0.9  # overload spike

    # -------- 5) FUSE ML + ACWR --------
    if acwr_component is None:
        final_probability = ml_probability
    else:
        # Weighted hybrid model
        final_probability = (0.6 * ml_probability) + (0.4 * acwr_component)

    final_probability = max(0.0, min(1.0, final_probability))  # clamp 0–1

    # -------- 6) RISK CLASSIFICATION --------
    if final_probability > 0.7:
        risk_level = "high"
    elif final_probability > 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    # -------- 7) PRESCRIPTIVE RECOMMENDATION ENGINE --------
    def build_recommendation(prob, acwr_val):
        if acwr_val and acwr_val > 1.5:
            return (
                "🚨 Load spike detected — VERY HIGH injury risk. "
                "Rest today. Reduce next week's workload by 40–60%. "
                "Avoid explosive sprinting and heavy lifting. "
                "Hydrate well and increase sleep duration."
            )
        if prob > 0.7:
            return (
                "❌ High injury risk. Avoid intense training today. "
                "Replace with mobility work, light stretching, and recovery runs."
            )
        elif prob > 0.4:
            return (
                "⚠️ Moderate risk. Reduce today's intensity by ~30%. "
                "Avoid max-effort jumps, sprints, and heavy squats."
            )
        else:
            return (
                "🟢 Low risk — safe to train. Maintain current progressions. "
                "Monitor soreness and keep sleep above 7.5 hours."
            )

    recommendation = build_recommendation(final_probability, acwr)

    # -------- 8) SAVE FINAL PREDICTION --------
    InjuryPrediction.objects.create(
        athlete=athlete,
        risk_level=risk_level,
        predicted_probability=final_probability,
        strain_score=strain_score,
        recommendation=recommendation,
        # ⬅️ NEW FIELD
    )

    # -------- 9) SEND RESPONSE TO FRONTEND --------
    return Response(
        {
            "status": "success",
            "athlete": athlete.name,
            "risk_level": risk_level,
            "probability": final_probability,
            "ml_probability": ml_probability,
            "acwr": acwr,

            "strain_score": strain_score,
            "recommendation": recommendation,  # ⬅️ NEW
        }
    )


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
    except AthleteData.DoesNotExist:
        return Response({"error": "Athlete not found"}, status=404)

    # Get most recent session
    session = (
        AthleteSession.objects.filter(athlete_id=athlete_id)
        .order_by("-session_date")
        .first()
    )
    if not session:
        return Response({"error": "No sessions found"}, status=404)

    # Compute ACWR safely
    try:
        acwr_val = float(athlete.acwr) if athlete.acwr is not None else None
    except:
        acwr_val = None

    payload = {
        "id": athlete.id,
        "name": athlete.name,
        "age": athlete.age,
        "sport": athlete.sport,
        "team": athlete.team,
        "experience_years": athlete.experience_years,

        # latest session metrics
        "heart_rate": session.heart_rate,
        "sleep_hours": session.sleep_hours,
        "steps": session.steps,
        "calories_burned": session.calories_burned,
        "intensity": session.calculated_intensity,
        "strain_score": session.strain_score,
        "fatigue_level": session.fatigue_level,

        # NEW — RETURN THESE SAFELY
        "acute_load": getattr(athlete, "acute_load", None),
        "chronic_load": getattr(athlete, "chronic_load", None),
        "acwr": acwr_val,
    }

    # Add averages (you already had this)
    payload.update(athlete.last_five_averages)

    return Response(payload, status=200)


@api_view(["GET"])
def athlete_history(request, athlete_id):
    try:
        athlete = AthleteData.objects.get(id=athlete_id)
        sessions = athlete.sessions.order_by("session_date")

        return Response([
            {
                "date": s.session_date.date().isoformat(),
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
