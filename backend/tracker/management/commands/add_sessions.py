from django.core.management.base import BaseCommand
from datetime import timedelta
import random
from backend.tracker.models import AthleteData, AthleteSession


class Command(BaseCommand):
    help = "Add 5 new realistic training sessions to every athlete"

    def handle(self, *args, **kwargs):
        DAYS_TO_ADD = 5

        for athlete in AthleteData.objects.all():
            last_session = (
                AthleteSession.objects.filter(athlete=athlete)
                .order_by("session_date")
                .last()
            )

            if not last_session:
                self.stdout.write(self.style.WARNING(
                    f"No sessions for {athlete.name}, skipping..."))
                continue

            start_date = last_session.session_date + timedelta(days=1)
            self.stdout.write(self.style.HTTP_INFO(
                f"\nAdding {DAYS_TO_ADD} sessions for {athlete.name}, starting {start_date.date()}"
            ))

            for i in range(DAYS_TO_ADD):
                date = start_date + timedelta(days=i)

                heart_rate = round(last_session.heart_rate +
                                   random.uniform(-4, 4), 2)
                sleep = round(
                    max(5.0, min(9.0, last_session.sleep_hours + random.uniform(-0.6, 0.6))), 2)
                steps = int(last_session.steps + random.randint(-1200, 2000))
                calories = max(350, steps * 0.058 + random.uniform(-80, 120))
                intensity = round(random.uniform(0.4, 1.3), 2)
                strain = round((steps / 1000) * intensity, 2)

                AthleteSession.objects.create(
                    athlete=athlete,
                    session_date=date,
                    heart_rate=heart_rate,
                    sleep_hours=sleep,
                    steps=steps,
                    calories_burned=round(calories, 2),
                    calculated_intensity=intensity,
                    fatigue_level=random.randint(0, 2),
                    strain_score=strain,
                    injury_occurred=random.choice([False, False, False, True]),
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✔ {date.date()} | HR={heart_rate} | Steps={steps} | Strain={strain}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(
            "\n🎯 DONE — Sessions added successfully!"))
