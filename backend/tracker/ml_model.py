import numpy as np


def predict_injury_risk(heart_rate, duration_minutes, calories_burned, calculated_intensity, strain_score):
    """
    Predict an injury risk score between 0 and 1 using a simple neural-inspired heuristic model.
    """

    # Normalize input data to prevent extreme scaling
    hr_factor = min(heart_rate / 180, 1)
    dur_factor = min(duration_minutes / 120, 1)
    cal_factor = min(calories_burned / 1000, 1)
    intensity_factor = min(calculated_intensity, 1)
    strain_factor = min(strain_score, 1)

    # Combine factors with realistic weights
    weighted_sum = (
        0.35 * hr_factor +
        0.25 * dur_factor +
        0.20 * intensity_factor +
        0.15 * strain_factor +
        0.05 * cal_factor
    )

    # Nonlinear activation (like a sigmoid neuron)
    risk_score = 1 / (1 + np.exp(-6 * (weighted_sum - 0.5)))

    return round(float(risk_score), 2)
