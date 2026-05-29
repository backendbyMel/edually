from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.http import HttpResponse
# Create your views here.
User = get_user_model()

class RegisterView(CreateView):
    """
    Handle user registration with email-based authentication.
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users away from registration page
        if request.user.is_authenticated:
            return HttpResponse("<h1>You are home!</h1>")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Save the user and add a success message
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Account created successfully! Please log in.'
        )
        return response
    
    def clean_middlename(self):
        middle_name = self.cleaned_data.get('middle_name')
        return middle_name


class CustomLoginView(LoginView):
    """
    Custom login view using email authentication.
    """
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        # Update last login timestamp
        response = super().form_valid(form)
        messages.success(self.request, f'Welcome back, {self.request.user.get_short_name()}!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """
    Handle user logout with a success message.
    """
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)

class ProfileView(LoginRequiredMixin, DetailView):
    """
    Display the current user's profile.
    """
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset=None):
        # Always return the logged-in user
        return self.request.user
    
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Allow users to update their profile information.
    """
    model = User
    template_name = 'users/profile_edit.html'
    fields = ['first_name','middle_name', 'last_name']
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

