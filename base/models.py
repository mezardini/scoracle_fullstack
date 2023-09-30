from django.db import models

# Create your models here.

class CSVFile(models.Model):
    # league = models.CharField(max_length=40)
    csv_file = models.FileField(upload_to='media')

