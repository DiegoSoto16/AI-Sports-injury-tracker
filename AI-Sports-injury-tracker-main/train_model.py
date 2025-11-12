import tensorflow as tf
import pandas as pd
import numpy as np

# Load dataset
data = pd.read_csv("injury_data.csv")

X = data[["heart_rate", "duration_minutes", "calories_burned", "calculated_intensity", "strain_score"]].values
y = data["injury"].values

# Normalize features
X = X / np.max(X, axis=0)

# Build model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation="relu", input_shape=(5,)),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(1, activation="sigmoid")  # binary classification
])

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

# Train
model.fit(X, y, epochs=20, batch_size=16, validation_split=0.2)

# Save model
model.save("backend/ml_models/injury_model.h5")
