from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    middle_name = forms.CharField(max_length=150,required=False)
    last_name = forms.CharField(max_length=150)
    school_name = forms.CharField(max_length=150)
    school_ID = forms.CharField(max_length=150)


    class Meta:
        model = User
        fields=['username','email','first_name','middle_name','last_name','password1','password2','school_name','school_ID']