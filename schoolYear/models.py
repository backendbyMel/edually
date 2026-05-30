from django.db import models

# Create your models here.
class schoolYear(models.Model):
    name = models.CharField(unique=True,max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True, verbose_name="Active Status")

    def __str__(self):
        return self.name