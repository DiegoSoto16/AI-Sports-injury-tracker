import numpy as np
import tensorflow as tf
from tensorflow import keras

# --- Step 1: Create training data (simulated athlete metrics) ---
# Each row = [heart_rate, steps, calories_burned, sleep_hours, fatigue_level, intensity_level]
X_train = np.random.rand(1000, 6)  # 1000 examples, 6 features

# Simulated injury risk (between 0 and 1)
y_train = np.random.rand(1000, 1)

# --- Step 2: Build the model ---
model = keras.Sequential([
    keras.layers.Dense(16, activation='relu', input_shape=(6,)),
    keras.layers.Dense(8, activation='relu'),
    # Output: risk score between 0 and 1
    keras.layers.Dense(1, activation='sigmoid')
])

# --- Step 3: Compile the model ---
model.compile(optimizer='adam', loss='mean_squared_error')

# --- Step 4: Train the model ---
model.fit(X_train, y_train, epochs=5, verbose=1)

# --- Step 5: Function to predict new athlete data ---


def predict_injury_risk(data):
    """
    data: list or array of [heart_rate, steps, calories_burned, sleep_hours, fatigue_level, intensity_level]
    returns: risk_score (float) and recommendation (string)
    """
    arr = np.array([data])
    # Use model prediction
    risk_score = float(model.predict(arr, verbose=0)[0][0])

    heart_rate, steps, calories, sleep, fatigue, intensity = data
    risk_score += (
        (heart_rate - 70) / 200 +
        (fatigue * 0.5) +
        (intensity * 0.3) -
        (sleep / 10)
    )
    risk_score = max(0.0, min(risk_score, 1.0))  # between 0 and 1

    if risk_score > 0.7:
        recommendation = "High injury risk! Reduce intensity or rest."
    elif risk_score > 0.4:
        recommendation = "Moderate risk. Monitor fatigue and recovery closely."
    else:
        recommendation = "Low risk. Continue regular training."

    return {"risk_score": round(risk_score, 2), "recommendation": recommendation}
