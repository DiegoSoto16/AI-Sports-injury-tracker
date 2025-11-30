from django.core.management.base import BaseCommand
from backend.tracker.models import AthleteData, AthleteSession
import random


class Command(BaseCommand):
    help = "Generate fake data for testing"

    def handle(self, *args, **kwargs):
        AthleteSession.objects.all().delete()
        AthleteData.objects.all().delete()

        print("Old data cleared.")

        names = [
            "Liam Johnson", "Noah Carter", "Ethan Brooks", "Mason Cooper",
            "Logan Rivera", "Ava Mitchell", "Sophia Turner", "Isabella Davis",
            "Mia Thompson", "Charlotte Lewis"
        ]

        sports = ["Soccer", "Basketball", "Football", "Tennis", "Track"]

        athletes = []

        for name in names:
            athlete = AthleteData.objects.create(
                name=name,
                age=random.randint(18, 25),
                sport=random.choice(sports),
                team="Team A",
                experience_years=round(random.uniform(1, 6), 1),
                heart_rate=0,
                duration_minutes=0,
                calories_burned=0,
                calculated_intensity=0,
                sleep_hours=0,
                steps=0,
                fatigue_level=0
            )
            athletes.append(athlete)

        print("10 athletes created.")

        athletes = AthleteData.objects.all()

        for athlete in athletes:
            for _ in range(25):

                heart_rate = random.uniform(70, 160)
                sleep_hours = random.uniform(4, 9)
                steps = random.randint(2000, 15000)
                calories = random.uniform(300, 1200)

                intensity = round(calories / 700, 2)
                strain = round(intensity * 10 + random.uniform(-1, 1), 2)

                AthleteSession.objects.create(
                    athlete=athlete,
                    heart_rate=heart_rate,
                    sleep_hours=sleep_hours,
                    steps=steps,
                    calories_burned=calories,
                    calculated_intensity=intensity,
                    fatigue_level=athlete.fatigue_level,  # Static fatigue
                    strain_score=strain,
                    injury_occurred=random.choice([False, False, False, True]),
                )

        print("All sessions created successfully!")
