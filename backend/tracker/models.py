from django.db import models

# Represents an athlete in the system


class Athlete(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    sport = models.CharField(max_length=50)
    team = models.CharField(max_length=100, blank=True, null=True)
    experience_years = models.IntegerField(default=0)

    def __str__(self):
        return self.name


# Stores injury predictions for each athlete
class InjuryPrediction(models.Model):
    athlete = models.ForeignKey(
        Athlete, on_delete=models.CASCADE, related_name='predictions')
    risk_score = models.FloatField()
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.athlete.name} - {self.risk_score:.2f}"
