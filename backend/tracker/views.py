from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AthleteData, InjuryPrediction, PredictionHistory
from .ml_model import predict_injury_risk


@api_view(['GET'])
def get_all_athletes(request):
    athletes = AthleteData.objects.all()
    data = [{
        "id": a.id,
        "name": a.name,
        "age": a.age,
        "sport": a.sport,
        "team": a.team,
        "experience_years": a.experience_years,
        "heart_rate": a.heart_rate,
        "duration_minutes": a.duration_minutes,
        "calories_burned": a.calories_burned,
        "calculated_intensity": a.calculated_intensity
    } for a in athletes]
    return Response(data)


@api_view(['POST'])
def predict_injury(request):
    data = request.data

    heart_rate = float(data.get("heart_rate"))
    duration_minutes = float(data.get("duration_minutes"))
    calories_burned = float(data.get("calories_burned"))
    experience_years = float(data.get("experience_years", 0))
    intensity = float(data.get("calculated_intensity", 1.0))

    # Run the AI risk model
    result = predict_injury_risk(
        heart_rate, duration_minutes, calories_burned, experience_years)

    # Save into InjuryPrediction
    athlete = AthleteData.objects.create(
        name=data.get("name", "Unknown"),
        age=data.get("age", 0),
        sport=data.get("sport", "Unknown"),
        team=data.get("team", "Unknown"),
        experience_years=experience_years,
        heart_rate=heart_rate,
        duration_minutes=duration_minutes,
        calories_burned=calories_burned,
        calculated_intensity=intensity
    )

    InjuryPrediction.objects.create(
        athlete=athlete,
        risk_level=result["risk_level"],
        predicted_probability=0.0,
        strain_score=result["strain_score"]
    )

    # Save in PredictionHistory too
    PredictionHistory.objects.create(
        athlete_name=data.get("name"),
        sport=data.get("sport"),
        team=data.get("team"),
        heart_rate=heart_rate,
        duration_minutes=duration_minutes,
        calories_burned=calories_burned,
        experience_years=experience_years,
        calculated_intensity=intensity,
        risk_level=result["risk_level"],
        strain_score=result["strain_score"]
    )

    return Response({
        "risk_level": result["risk_level"],
        "strain_score": result["strain_score"]
    })


@api_view(['GET'])
def get_prediction_history(request):
    history = PredictionHistory.objects.all().order_by('-created_at')
    data = [
        {
            "athlete_name": h.athlete_name,
            "sport": h.sport,
            "team": h.team,
            "heart_rate": h.heart_rate,
            "duration_minutes": h.duration_minutes,
            "calories_burned": h.calories_burned,
            "experience_years": h.experience_years,
            "calculated_intensity": h.calculated_intensity,
            "risk_level": h.risk_level,
            "strain_score": h.strain_score,
            "created_at": h.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for h in history
    ]
    return Response(data)
