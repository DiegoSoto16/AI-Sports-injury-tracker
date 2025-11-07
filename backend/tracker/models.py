from django.db import models


class AthleteData(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    sport = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    experience_years = models.FloatField()
    heart_rate = models.FloatField()
    duration_minutes = models.FloatField()
    calories_burned = models.FloatField()
    calculated_intensity = models.FloatField()
    sleep_hours = models.FloatField(default=0.0)
    steps = models.IntegerField(default=0)
    fatigue_level = models.IntegerField(default=0)

    def __str__(self):
        return self.name


# Core prediction results table
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
