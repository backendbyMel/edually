from django.db import models
from enrollment.models import Enrollment
from term.models import Term
# Create your models here.
STATUS_CHOICES = [
    ('P', 'Present'),
    ('A', 'Absent'),
    ('L', 'Late'),
    ('E', 'Excused'),
]
class Attendance(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    term= models.ForeignKey(Term, on_delete=models.CASCADE)
    date= models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,default='P')
    remarks = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = ['enrollment', 'date','term']
        ordering = ['-date']

    def __str__(self):
        return str(self.date)