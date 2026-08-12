from django.db import models
from django.contrib.auth.models import User

class PromptVariant(models.Model):
    """A system prompt variant to test."""
    name = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    times_tested = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} (score: {self.score})"

class PromptEvaluation(models.Model):
    """Evaluation of a prompt variant on a specific conversation."""
    variant = models.ForeignKey(PromptVariant, on_delete=models.CASCADE)
    conversation = models.TextField()  # The chat history used for evaluation
    score = models.FloatField()
    evaluated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.variant.name} - {self.score:.2f}"