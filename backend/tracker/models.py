from django.db import models
import datetime


class AthleteData(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    sport = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    experience_years = models.FloatField()

    # kept for compatibility
    heart_rate = models.FloatField(default=0)
    duration_minutes = models.FloatField(default=0)
    calories_burned = models.FloatField(default=0)
    calculated_intensity = models.FloatField(default=0)
    sleep_hours = models.FloatField(default=0)
    steps = models.IntegerField(default=0)
    fatigue_level = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @property
    def last_five_sessions(self):
        return self.sessions.order_by("-session_date")[:5]

    @property
    def avg_heart_rate(self):
        sessions = self.last_five_sessions
        if not sessions:
            return 0
        return round(sum(s.heart_rate for s in sessions) / len(sessions), 2)

    @property
    def avg_sleep_hours(self):
        sessions = self.last_five_sessions
        if not sessions:
            return 0
        return round(sum(s.sleep_hours for s in sessions) / len(sessions), 2)

    @property
    def avg_steps(self):
        sessions = self.last_five_sessions
        if not sessions:
            return 0
        return round(sum(s.steps for s in sessions) / len(sessions), 2)

    @property
    def avg_calories_burned(self):
        sessions = self.last_five_sessions
        if not sessions:
            return 0
        return round(sum(s.calories_burned for s in sessions) / len(sessions), 2)

    @property
    def avg_intensity(self):
        sessions = self.last_five_sessions
        if not sessions:
            return 0
        return round(sum(s.calculated_intensity for s in sessions) / len(sessions), 2)

    @property
    def avg_strain(self):
        sessions = self.last_five_sessions
        if not sessions:
            return 0
        return round(sum(s.strain_score for s in sessions) / len(sessions), 2)


class AthleteSession(models.Model):
    athlete = models.ForeignKey(
        AthleteData, on_delete=models.CASCADE, related_name="sessions"
    )

    session_date = models.DateTimeField(default=datetime.datetime.now)

    heart_rate = models.FloatField()
    sleep_hours = models.FloatField()
    steps = models.IntegerField()
    calories_burned = models.FloatField()
    calculated_intensity = models.FloatField()
    fatigue_level = models.IntegerField(default=0)
    strain_score = models.FloatField()

    #  ML training later
    injury_occurred = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.athlete.name} – Session on {self.session_date.date()}"


class InjuryPrediction(models.Model):
    athlete = models.ForeignKey(AthleteData, on_delete=models.CASCADE)
    risk_level = models.CharField(max_length=50)
    predicted_probability = models.FloatField(default=0.0)
    strain_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.athlete.name} - {self.risk_level}"


class PredictionHistory(models.Model):
    name = models.CharField(max_length=100, default="Unknown")
    sport = models.CharField(max_length=100, default="Unknown")
    team = models.CharField(max_length=100, null=True, blank=True, default="")
    heart_rate = models.FloatField()
    duration_minutes = models.FloatField()
    calories_burned = models.FloatField()
    experience_years = models.FloatField(default=0)
    calculated_intensity = models.FloatField()
    risk_level = models.CharField(max_length=20)
    strain_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
