from django.db import models
from django.contrib.auth.models import User

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    metric = models.CharField(max_length=50)  # e.g., 'cpu', 'ram', 'build_success'
    value = models.FloatField()
    confidence = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.metric}: {self.value}"

class StrategicAdvice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50)  # e.g., 'system', 'knowledge', 'build'
    message = models.TextField()
    action_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.category}: {self.message[:50]}"