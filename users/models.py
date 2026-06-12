from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    middle_name = models.CharField(max_length=150, blank=True)
    has_seen_guide = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} Profile'
    

