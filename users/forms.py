from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
            'autocomplete': 'email'
        })
    )

    first_name = forms.CharField(
        label='First Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )

    middle_name = forms.CharField(
        label='Middle Name',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Middle name'
        })
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    class Meta:
        model = User
        fields = ('email', 'first_name','middle_name', 'last_name', 'password1', 'password2')

    
    def clean_email(self):
        """Normalize and validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()  # Normalize to lowercase
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email already exists.')
        return email
            
    def save(self, commit=True):
        """Save the user with normalized email"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
            'autocomplete': 'email',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )

    error_messages = {
        'invalid_login': 
            'Please enter a correct email and password. Note that both fields are case-sensitive.'
        
        ,
        
    }

