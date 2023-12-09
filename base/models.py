from django.db import models

# Create your models here.


class Prediction(models.Model):
    # league = models.CharField(max_length=40)
    content = models.JSONField(null=True)
    league = models.CharField(max_length=50, null=True)
    date = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return 'Predictions of ' + str(self.date)
