from django.db import models
from schoolYear.models import schoolYear
from datetime import date
# Create your models here.
class Term(models.Model):
    school_year= models.ForeignKey(schoolYear, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    start_date=models.DateField()
    end_date=models.DateField()
    is_current  = models.BooleanField(default=False, verbose_name="Current Term")

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.is_current = self.start_date <= date.today() <= self.end_date
        super().save(*args, **kwargs)
