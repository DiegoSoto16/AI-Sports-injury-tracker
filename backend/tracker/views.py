from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Athlete, InjuryPrediction
from .serializers import AthleteSerializer, InjuryPredictionSerializer
import numpy as np
import tensorflow as tf

# Simple AI model placeholder (used earlier for predictions)
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(5,)),
    tf.keras.layers.Dense(8, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy')


@api_view(['POST'])
def predict_view(request):
    """
    Receives athlete data via POST, predicts injury risk using TensorFlow,
    saves results to the database, and returns a JSON response.
    """
    try:
        data = request.data
        athlete_id = data.get('athlete_id')

        # Ensure athlete exists
        if not athlete_id:
            return Response({"error": "athlete_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            athlete = Athlete.objects.get(id=athlete_id)
        except Athlete.DoesNotExist:
            return Response({"error": f"No athlete found with id {athlete_id}"}, status=status.HTTP_404_NOT_FOUND)

        # Prepare features
        features = np.array([
            data.get('training_hours', 0),
            data.get('intensity', 0),
            data.get('sleep_hours', 0),
            data.get('hydration_level', 0),
            data.get('previous_injuries', 0)
        ]).reshape(1, -1)

        # Run TensorFlow model
        prediction = float(model.predict(features, verbose=0)[0][0])
        risk_score = round(prediction * 100, 2)

        # Determine recommendation
        if risk_score < 33:
            recommendation = "Low risk. Continue regular training."
        elif 33 <= risk_score < 66:
            recommendation = "Moderate risk. Adjust training intensity."
        else:
            recommendation = "High risk! Consider rest and assessment."

        # Save prediction linked to the athlete
        InjuryPrediction.objects.create(
            athlete=athlete,
            risk_score=risk_score,
            recommendation=recommendation
        )

        return Response({
            "athlete": athlete.name,
            "risk_score": risk_score,
            "recommendation": recommendation
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_all_predictions(request):
    """Fetches all saved injury predictions from the database."""
    predictions = InjuryPrediction.objects.all().order_by('-created_at')
    serializer = InjuryPredictionSerializer(predictions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_all_athletes(request):
    """Fetches all athlete data entries."""
    athletes = Athlete.objects.all()
    serializer = AthleteSerializer(athletes, many=True)
    return Response(serializer.data)
