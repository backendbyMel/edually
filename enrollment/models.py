from django.db import models
from sections.models import Section
from students.models import Student
# Create your models here.

class Enrollment(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
