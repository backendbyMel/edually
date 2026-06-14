from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Student
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .forms import AddStudentForm
from django.db.models import Q
from enrollment.models import Enrollment
# Create your views here.
class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    field = ['lrn','first_name','middle_name','last_name','gender','date_of_birth','age','birth_cert']
    template_name = 'students/student_home.html'
    context_object_name = 'students'
    paginate_by = 8

    def get_queryset(self):
        queryset = Student.objects.filter(added_by=self.request.user)
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(lrn__icontains=q) |
                Q(first_name__icontains=q) |
                Q(middle_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        return queryset
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
                "A student with this LRN already exists"
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        enrollments = Enrollment.objects.filter(student=student)
        context['enrollments'] = enrollments
        context['total_enrollments'] = enrollments.count()

        # Attendance summary
        from attendance.models import Attendance
        attendances = Attendance.objects.filter(
            enrollment__student=student
        )
        total = attendances.count()
        present = attendances.filter(status='P').count()
        context['total_present'] = present
        context['total_absent'] = attendances.filter(status='A').count()
        context['total_late'] = attendances.filter(status='L').count()
        context['total_excused'] = attendances.filter(status='E').count()
        context['attendance_percentage'] = round(
            present / total * 100, 1
        ) if total > 0 else None
        context['is_at_risk'] = (
            context['attendance_percentage'] < 80
        ) if context['attendance_percentage'] else False

        

        return context

    def test_func(self):
        student = self.get_object()
        if self.request.user == student.added_by:
            return True
        return False

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = AddStudentForm
    template_name = 'students/student_update.html'
    
    
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

