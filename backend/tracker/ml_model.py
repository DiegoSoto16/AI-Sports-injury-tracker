import math


def predict_injury_risk(heart_rate, duration_minutes, calories_burned, experience_years):
    #  Calculate training load (how intense the session was)
    training_load = (heart_rate * duration_minutes * 0.1) + \
        (calories_burned * 0.05)

    #  Use experience to reduce risk slightly
    adjusted_load = training_load / (1 + (experience_years * 0.1))

    #  Calculate strain score
    strain_score = round(adjusted_load / 100, 2)

    #  Determine risk level realistically
    if strain_score < 2.5:
        risk = "low"
    elif strain_score < 5.0:
        risk = "medium"
    else:
        risk = "high"

    return {
        "risk_level": risk,
        "strain_score": strain_score
    }
