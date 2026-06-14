from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    middle_name = forms.CharField(max_length=150,required=False)
    last_name = forms.CharField(max_length=150)


    class Meta:
        model = User
        fields=['username','email','first_name','middle_name','last_name','password1','password2']

    def clean_email(self):
        email = self.cleaned_data["email"]

        if not email:
            raise forms.ValidationError(
                'Email is required.'
            )

        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'This email address is already registered. '
                'Please use a different email or log in.'
            )

        return email

class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"]

        if not email:
            raise forms.ValidationError(
                'Email is required.'
            )

        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'This email address is already registered. '
                'Please use a different email or log in.'
            )

        return email

class NameChangeForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    middle_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)