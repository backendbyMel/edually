from django import forms
from .models import schoolYear

class schoolYearform(forms.ModelForm):
    class Meta:
        model = schoolYear
        fields = '__all__'
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }