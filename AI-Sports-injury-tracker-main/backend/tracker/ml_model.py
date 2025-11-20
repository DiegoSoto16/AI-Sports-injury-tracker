import tensorflow as tf
import numpy as np

# Load pre-trained model
model = tf.keras.models.load_model("backend/ml_models/injury_model.h5")

def predict_injury_risk(heart_rate, duration_minutes, calories_burned, calculated_intensity, strain_score):
    features = np.array([[heart_rate, duration_minutes, calories_burned, calculated_intensity, strain_score]])
    prediction = model.predict(features)
    return round(float(prediction[0][0]), 2)
