from django.db import connection
from tracker.models import AthleteData, InjuryPrediction
import random


def reset_sequences():
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM sqlite_sequence WHERE name='tracker_athletedata';")
        cursor.execute(
            "DELETE FROM sqlite_sequence WHERE name='tracker_injuryprediction';")


print(" Deleting old data...")
InjuryPrediction.objects.all().delete()
AthleteData.objects.all().delete()
reset_sequences()


athletes = [
    {"name": "Liam Johnson", "age": 22, "sport": "Soccer",
        "team": "C", "experience_years": 3.5},
    {"name": "Emma Smith", "age": 24, "sport": "Soccer",
        "team": "A", "experience_years": 4.0},
    {"name": "Noah Brown", "age": 23, "sport": "Soccer",
        "team": "B", "experience_years": 2.8},
    {"name": "Ava Martinez", "age": 25, "sport": "Basketball",
        "team": "C", "experience_years": 5.1},
    {"name": "Olivia Lopez", "age": 21, "sport": "Track",
        "team": "B", "experience_years": 2.0},
    {"name": "Ethan Taylor", "age": 26, "sport": "Soccer",
        "team": "C", "experience_years": 6.2},
    {"name": "Sophia Anderson", "age": 22, "sport": "Basketball",
        "team": "A", "experience_years": 3.2},
    {"name": "James Davis", "age": 24, "sport": "Soccer",
        "team": "B", "experience_years": 4.3},
    {"name": "Isabella Wright", "age": 23, "sport": "Track",
        "team": "C", "experience_years": 3.9},
    {"name": "Mason Green", "age": 27, "sport": "Soccer",
        "team": "A", "experience_years": 7.1},
]


print(" Generating sample athletes and injury predictions...")

for athlete in athletes:
    try:
        print(f"Seeding athlete: {athlete['name']} ...")

        # realistic random performance data
        heart_rate = random.uniform(65, 105)
        duration = random.uniform(40, 90)
        calories = round(duration * (heart_rate / 10), 2)
        sleep_hours = round(random.uniform(5.0, 9.0), 1)
        steps = random.randint(4000, 15000)

        # Derived metrics
        intensity = round((heart_rate / 200) + (duration / 120), 2)
        strain = round(((steps / 10000) + (heart_rate / 200)) / 2, 2)

        # athlete record
        a = AthleteData.objects.create(
            name=athlete["name"],
            age=athlete["age"],
            sport=athlete["sport"],
            team=athlete["team"],
            experience_years=athlete["experience_years"],
            heart_rate=heart_rate,
            duration_minutes=duration,
            calories_burned=calories,
            calculated_intensity=intensity,
            sleep_hours=sleep_hours,
            steps=steps,
        )

        # Normalize factors
        heart_factor = heart_rate / 200
        strain_factor = strain
        sleep_factor = max(0, 1 - (sleep_hours / 8))
        steps_factor = max(0, 1 - (steps / 12000))
        intensity_factor = intensity / 10

        # Weighted risk model emphasizing fatigue/stress
        risk_score = round((
            (heart_factor * 0.30) +
            (strain_factor * 0.30) +
            (sleep_factor * 0.20) +
            (steps_factor * 0.10) +
            (intensity_factor * 0.10)
        ), 2)

        risk_score = round(min(risk_score * 1.4, 1.0), 2)

        # Risk categories
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.45:
            risk_level = "medium"
        else:
            risk_level = "low"

        InjuryPrediction.objects.create(
            athlete=a,
            risk_level=risk_level,
            predicted_probability=risk_score,
            strain_score=strain,
        )

        print(
            f" Created {a.name} ({a.sport}) → Risk: {risk_level} ({risk_score})")

    except Exception as e:
        print(f" Error for {athlete['name']}: {e}")

print("\n Done! 10 athletes and predictions seeded successfully.")
