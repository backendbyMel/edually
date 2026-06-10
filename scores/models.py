from django.db import models
from sections.models import Subject
from term.models import Term
from enrollment.models import Enrollment
# Create your models here.
COMPONENT_TYPE = [
    ('WW', 'Written Works'),
    ('PT', 'Performance Tasks'),
    ('TE', 'Term Exam'),
]

ACTIVITY_TYPE = [
    ('graded', 'Graded Activity'),
    ('compliance', 'Compliance Check'),
    ('recorded', 'Recorded Only'),
]

class Activity(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=1000)
    component = models.CharField(choices=COMPONENT_TYPE, null=True, blank=True)
    activity_type = models.CharField(choices=ACTIVITY_TYPE, default='graded')
    total_score = models.IntegerField(null=True,blank=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.subject.name}"


class Score(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    score = models.DecimalField(null=True, blank=True,max_digits = 5, decimal_places=2)
    is_complied = models.BooleanField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ['activity', 'enrollment']

    def __str__(self):
        return f"{self.enrollment.student} - {self.activity.title}"
