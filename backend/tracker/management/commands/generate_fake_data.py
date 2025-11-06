from django.core.management.base import BaseCommand
from tracker.models import AthleteData, InjuryPrediction
from tracker.ml_model import predict_injury_risk
from faker import Faker
import random


class Command(BaseCommand):
    help = "Generate fake athlete data with predictions"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10,
                            help="Number of fake athletes to create")

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]

        self.stdout.write(f"Generating {count} fake athlete records...")

        for _ in range(count):
            # Randomized training metrics
            heart_rate = random.uniform(60, 180)
            duration = random.uniform(20, 120)
            calories = random.uniform(200, 900)
            calculated_intensity = round(random.uniform(0.2, 1.2), 2)
            strain_score = round(random.uniform(0.3, 1.0), 2)

            # Create athlete entry
            athlete = AthleteData.objects.create(
                name=fake.name(),
                age=random.randint(18, 25),
                sport=random.choice(
                    ["Soccer", "Basketball", "Baseball", "Track", "Tennis"]),
                team=random.choice(
                    ["Shepherd Rams", "WV Hornets", "DC Spartans"]),
                experience_years=random.randint(1, 10),
                heart_rate=heart_rate,
                duration_minutes=duration,
                calories_burned=calories,
                calculated_intensity=calculated_intensity,
            )

            # Predict risk using ML model
            risk_score = predict_injury_risk(
                heart_rate, duration, calories, calculated_intensity, strain_score)

            if risk_score > 0.7:
                risk_level = "high"
            elif risk_score > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Create corresponding injury prediction
            InjuryPrediction.objects.create(
                athlete=athlete,
                risk_level=risk_level,
                predicted_probability=risk_score,
                strain_score=strain_score,
            )

        self.stdout.write(self.style.SUCCESS(
            f" Successfully created {count} fake athletes and predictions!"))
