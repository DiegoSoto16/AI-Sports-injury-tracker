import os
import joblib
import tensorflow as tf
import numpy as np

# BASE_DIR = backend/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ml_models is directly inside backend/
ML_DIR = os.path.join(os.path.dirname(BASE_DIR), "ml_models")

SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")
MODEL_PATH = os.path.join(ML_DIR, "injury_model.h5")

# Load model + scaler
scaler = joblib.load(SCALER_PATH)
model = tf.keras.models.load_model(MODEL_PATH)


def predict_injury(heart_rate, sleep_hours, steps, calories_burned, intensity, strain_score):

    # Prepare vector
    X = np.array(
        [[heart_rate, sleep_hours, steps, calories_burned, intensity, strain_score]])

    # Scale input
    X_scaled = scaler.transform(X)

    # Predict probability
    probability = float(model.predict(X_scaled)[0][0])

    return probability
