from django.db import models
from django.contrib.auth.models import User
from schoolYear.models import schoolYear
from term.models import Term
from django.urls import reverse

CLASS_TYPE_CHOICES = [
    ("JHS", "Junior High School"),
    ("SHS", "Senior High School"),
]

SUBJECT_TYPE_CHOICES = [
    #for JHS 
    ('jhs_regular', 'JHS - Regular Subject'),
    ('jhs_tle_mapeh', 'JHS - TLE / MAPEH'),
    #for SHS
    ('core', 'Core'),
    ('academic_elective', 'Academic Elective - All Other'),
    ('academic_field', 'Academic Elective - Field/Exposure/Sports/Arts'),
    ('techpro_elective', 'TechPro Elective - All Other'),
    ('techpro_immersion', 'TechPro Elective - Work Immersion'),
]

GRADE_LEVEL_CHOICES = [
    ('7', 'Grade 7'),
    ('8', 'Grade 8'),
    ('9', 'Grade 9'),
    ('10', 'Grade 10'),
    ('11', 'Grade 11'),
    ('12', 'Grade 12'),
]
# Create your models here.
class Section(models.Model):
    adviser = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, null=True)
    grade_level = models.CharField(max_length=2,choices=GRADE_LEVEL_CHOICES,null=True,blank=True)
    class_type = models.CharField(max_length=100, choices=CLASS_TYPE_CHOICES, default='JHS',null=True)
    is_adviser = models.BooleanField(default=True) 
    is_subject_teacher = models.BooleanField(default=False)
    school_name=models.CharField(max_length=100, verbose_name="School Name")
    school_id=models.CharField(max_length=50, verbose_name="School ID")
    principal_name = models.CharField(max_length=100, null=True, verbose_name="Principal Name", help_text="for SF9 purposes")
    region = models.CharField(max_length=150)
    division = models.CharField(max_length=150)
    school_year = models.ForeignKey(schoolYear,on_delete=models.CASCADE, limit_choices_to= {'is_active':True}, default='S.Y. 2026-2027') 
    

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('section-detail', kwargs={'pk':self.pk})

class Subject(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    subject_type = models.CharField(max_length=20,choices=SUBJECT_TYPE_CHOICES,default='core')
    order = models.IntegerField(help_text="Order is for SF9 purposes if you are adviser. If not please put random number.")
    is_handled_by_owner = models.BooleanField(default=False, verbose_name="I am the subject teacher for this",help_text="Check this if you personally teach this subject. \nGrades will be auto-computed from scores you encode. \nLeave unchecked if another teacher handles this subject \nand you will manually input the final grade.")

    def __str__(self):
        return self.name