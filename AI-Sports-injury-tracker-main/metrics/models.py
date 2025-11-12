from django.db import models

# Create your models here.
class WearableData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    heart_rate = models.IntegerField()
    fatigue_level = models.IntegerField()
    sleep_hours = models.FloatField()
    steps = models.IntegerField()

    def __str__(self):
        return f"Data @ {self.timestamp}"