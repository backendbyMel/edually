from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
# Create your models here.

Gender_Choices = {
    "F": "Female",
    "M": "Male",
}
Birthcert_Choices = {
    "Y": "With Birth Certificate",
    "N": "No Birth Certificate",
}
class Student(models.Model):
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    lrn = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100,null=True,blank=True)
    last_name = models.CharField(max_length=100)
    complete_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender_Choices, default='F')
    date_of_birth = models.DateField()
    age = models.IntegerField(null=True,blank=True, help_text="Manually input the age for SF9 purposes")
    birth_cert = models.CharField(max_length=5, choices=Birthcert_Choices, default='Y')

    class Meta:
        unique_together = ['added_by', 'lrn']

    def save(self, *args, **kwargs):
        if self.middle_name!='' or self.middle_name!='None':
            self.complete_name = f"{self.first_name} {self.middle_name} {self.last_name}".strip()
        else:
            self.complete_name = f"{self.first_name} {self.last_name}".strip()
        super(Student, self).save(*args, **kwargs)

    def __str__(self):
        return self.lrn + " " + self.complete_name