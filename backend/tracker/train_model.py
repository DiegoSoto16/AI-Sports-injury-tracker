# isort:skip_file

import os
import sys
import django
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import tensorflow as tf


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


def load_models():
    from tracker.models import AthleteSession
    return AthleteSession


AthleteSession = load_models()


# Load session dataset

print("Loading data from database...")

sessions = AthleteSession.objects.all().values(
    "heart_rate",
    "sleep_hours",
    "steps",
    "calories_burned",
    "calculated_intensity",
    "strain_score",
    "injury_occurred",
)

data = pd.DataFrame(list(sessions))

if data.empty:
    raise ValueError(
        " ERROR: No AthleteSession records found. Run generate_fake_data first.")


X = data[
    [
        "heart_rate",
        "sleep_hours",
        "steps",
        "calories_burned",
        "calculated_intensity",
        "strain_score",
    ]
].values

y = data["injury_occurred"].astype(int).values


print("Normalizing...")

scaler = StandardScaler()
X = scaler.fit_transform(X)

# Ensure directory exists
MODEL_DIR = os.path.join(BASE_DIR, "backend", "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))


# Build Keras model

print("Training model...")

model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation="relu", input_shape=(6,)),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(1, activation="sigmoid"),  # Binary classification
])

model.compile(optimizer="adam", loss="binary_crossentropy",
              metrics=["accuracy"])

model.fit(X, y, epochs=20, batch_size=16, validation_split=0.2)


model.save(os.path.join(MODEL_DIR, "injury_model.h5"))

print(" Model trained and saved successfully!")
