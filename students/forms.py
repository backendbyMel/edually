from django import forms
from .models import Student
from django.core.exceptions import ValidationError 

class AddStudentForm(forms.ModelForm):
    middle_name = forms.CharField(max_length=150, required=False)
    
    class Meta:
        model = Student
        fields = ['lrn','first_name','middle_name','last_name','gender','date_of_birth','age','birth_cert']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'text',        # Important: use 'text' not 'date'
                'autocomplete': 'off',
                'readonly': 'readonly',
            }),
        }