from django.db import models
import datetime
from datetime import timedelta
from django.utils.timezone import now


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

    @property
    def last_five_averages(self):
        """
        Returns a dict of rolling averages from last five sessions.
        Used by latest_session endpoint to attach summary metrics.
        """
        return {
            "avg_heart_rate": self.avg_heart_rate,
            "avg_sleep_hours": self.avg_sleep_hours,
            "avg_steps": self.avg_steps,
            "avg_calories_burned": self.avg_calories_burned,
            "avg_intensity": self.avg_intensity,
            "avg_strain": self.avg_strain,
        }

    @property
    def acute_load(self):
        """
        Sum of strain scores for the last 7 days (short-term load).
        """
        last_week = now() - timedelta(days=7)
        sessions = self.sessions.filter(session_date__gte=last_week)
        if not sessions:
            return 0
        return round(sum(s.strain_score for s in sessions), 2)


@property
def chronic_load(self):
    """
    Average weekly load for the past 28 days (long-term load).
    """
    last_month = now() - timedelta(days=28)
    sessions = self.sessions.filter(session_date__gte=last_month)
    if not sessions:
        return 1  # avoid division by zero

    weekly_avg = sum(s.strain_score for s in sessions) / 4
    return round(weekly_avg, 2)


@property
def acwr(self):
    """
    Acute:Chronic Workload Ratio
    ACWR = acute_load / chronic_load
    Safe Zone: 0.8 - 1.3
    Danger Zone: >1.5
    Underloaded: <0.8
    """
    if self.chronic_load == 0:
        return 1.0
    return round(self.acute_load / self.chronic_load, 2)


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
    recommendation = models.TextField(default="", blank=True)

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
