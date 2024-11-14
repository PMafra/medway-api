from django.db import models

from question.utils import AlternativesChoices


class Question(models.Model):
    content = models.TextField()

    def __str__(self):
        return self.content


class Alternative(models.Model):
    question = models.ForeignKey(
        Question, related_name="alternatives", on_delete=models.CASCADE
    )
    content = models.TextField()
    option = models.IntegerField(choices=AlternativesChoices)
    is_correct = models.BooleanField(null=True)

    def __str__(self):
        return self.content
