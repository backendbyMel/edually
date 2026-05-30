from django.db import models
from django.contrib.auth.models import User
from schoolYear.models import schoolYear

teacherAssignment = {
    "advisory": "Adviser",
    "subjectTeacher": "Subject Teacher"
}

# Create your models here.
class Section(models.Model):
    adviser = models.ForeignKey(User, on_delete=models.CASCADE)
    principal_name = models.CharField(max_length=100, null=True)
    school_year = models.ForeignKey(schoolYear,on_delete=models.CASCADE, limit_choices_to = {'is_active':True})
    name = models.CharField(max_length=20, null=True)
    role = models.CharField(max_length=50, choices=teacherAssignment, default='subjectTeacher')

    def __str__(self):
        return self.name
