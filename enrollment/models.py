from django.db import models
from sections.models import Section
from students.models import Student
from django.contrib.auth.models import User
# Create your models here.

status = {
    "transferee": "Transferee",
    "regular_student": "Regular Student",
    "returnee": "Returnee",
}

class Enrollment(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)