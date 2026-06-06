from django.db import models
from django.contrib.auth.models import User
from schoolYear.models import schoolYear
from term.models import Term
from django.urls import reverse

Class_Type = {
    "JHS": "Junior High School",
    "SHS": "Senior High School",
}
# Create your models here.
class Section(models.Model):
    adviser = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, null=True)
    grade_level = models.IntegerField(null=True)
    class_type = models.CharField(max_length=100, choices=Class_Type, default='JHS',null=True)
    is_adviser = models.BooleanField(default=True) 
    is_subject_teacher = models.BooleanField(default=False)
    principal_name = models.CharField(max_length=100, null=True)
    school_year = models.ForeignKey(schoolYear,on_delete=models.CASCADE, limit_choices_to= {'is_active':True}, default='S.Y. 2026-2027') 
    

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('section-detail', kwargs={'pk':self.pk})

class Subject(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    is_handled_by_owner = models.BooleanField(default=False, verbose_name="I am the subject teacher for this",help_text="Check this if you personally teach this subject. \nGrades will be auto-computed from scores you encode. \nLeave unchecked if another teacher handles this subject \nand you will manually input the final grade.")

    def __str__(self):
        return self.name