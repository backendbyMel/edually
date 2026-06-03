from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Student
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .forms import AddStudentForm
# Create your views here.
class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    field = ['lrn','first_name','middle_name','last_name','gender','date_of_birth','age','birth_cert']
    template_name = 'students/student_home.html'
    context_object_name = 'students'

    def get_queryset(self):
        return Student.objects.filter(added_by=self.request.user)

class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = AddStudentForm
    template_name = 'students/student_create.html'
    success_url = reverse_lazy('student-home') 
    
    def form_valid(self, form):
        try:
            # Set the added_by field before saving
            form.instance.added_by = self.request.user
            return super().form_valid(form)
            
        except IntegrityError:
            form.add_error(
                'lrn', 
                "A student with this LRN already exists for your account."
            )
            return self.form_invalid(form)
    
    def get_form(self):
        form = super().get_form()
        form.fields["date_of_birth"].widget = DatePickerInput()
        return form
    

class StudentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def test_func(self):
        student = self.get_object()
        if self.request.user == student.added_by:
            return True
        return False

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = AddStudentForm
    template_name = 'students/student_update.html'
    
    def get_form_kwargs(self):
        # 1. Get the dictionary of default arguments from the parent class
        kwargs = super().get_form_kwargs()
        
        # 2. Inject your custom dynamic data (e.g., the current request user)
        kwargs['user'] = self.request.user
        
        # 3. Return the modified dictionary
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('student-detail', kwargs={'pk': self.kwargs['pk']})

    def get_object(self, queryset=None):
        return get_object_or_404(Student, pk=self.kwargs['pk'])

    def test_func(self):
        student = self.get_object()
        if self.request.user == student.added_by:
            return True
        return False

class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    success_url = reverse_lazy('student-home') 
    template_name = "students/student_confirm_delete.html"

    def test_func(self):
        section = self.get_object()
        if self.request.user == section.added_by:
            return True
        return False

