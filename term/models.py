from django.db import models
from schoolYear.models import schoolYear
# Create your models here.
class Term(models.Model):
    school_year= models.ForeignKey(schoolYear, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    start_date=models.DateField()
    end_date=models.DateField()
    is_active = models.BooleanField(default=True, verbose_name="Active Status")

    def __str__(self):
        return self.name
