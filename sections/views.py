from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Section, Subject
from enrollment.models import Enrollment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from attendance.models import Attendance
import datetime
from attendance.views import get_term_months
from term.models import Term
from attendance.views import calculate_school_days
# Create your views here.
class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'sections/section_home.html'
    context_object_name = 'sections'

    def get_queryset(self):
        return Section.objects.filter(adviser=self.request.user)

class SectionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Section
    template_name = 'sections/section_detail.html'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['term_months'] = get_term_months()
        context['enrollments'] = Enrollment.objects.filter(
            section=self.get_object()
        ).order_by('student__last_name','student__gender')

        context['subjects'] = Subject.objects.filter(
            section=self.object
        ).order_by('order')
        
        # Attendance quick stats
        today = datetime.date.today()
        enrollments = context['enrollments']
        total_students = enrollments.count()

        # Check if today's attendance is recorded
        today_attendance = Attendance.objects.filter(
            enrollment__section=self.object,
            date=today
        ).count()
        
        active_term = Term.objects.filter(
                start_date__lte=today,
                end_date__gte=today,
                is_current=True,
            ).first()
        
        total_school_days = 0
        if active_term:
            # Get the specific term dates
            term_obj = get_object_or_404(Term, pk=active_term.id)
            total_school_days = calculate_school_days(term_obj.start_date, term_obj.end_date)
        else:
            total_school_days = 0
            for term_obj in Term.objects.all():
                total_school_days += calculate_school_days(term_obj.start_date, term_obj.end_date)
        
        is_school_day = active_term is not None and today.weekday() < 5


        if is_school_day:
            today_attendance = Attendance.objects.filter(
                enrollment__section=self.object,
                date=today,
            ).count()
            context['today_recorded'] = total_students > 0 and today_attendance >= total_students
            context['today_present'] = Attendance.objects.filter(
                enrollment__section=self.object,
                date=today,
                status='P',
            ).count()
            context['today_absent'] = Attendance.objects.filter(
                enrollment__section=self.object,
                date=today,
                status='A',
            ).count()
        else:
            # Outside term or weekend — suppress the warning entirely
            context['today_recorded'] = True   # prevents warning from showing
            context['today_present'] = 0
            context['today_absent'] = 0

        context['is_school_day'] = is_school_day
        context['active_term'] = active_term
        context['total_students'] = total_students

        
        
        at_risk_count = 0
        for enrollment in enrollments:
            total = Attendance.objects.filter(
                enrollment=enrollment
            ).count()
            absent = Attendance.objects.filter(
                    enrollment=enrollment,
                    status='A',
                ).count()
            if total > 0 and (absent / total_school_days) * 100 > 20:
                at_risk_count += 1

        
        context['at_risk_count'] = at_risk_count  # hint: compute this
        return context

    def test_func(self):
        section = self.get_object()
        if self.request.user == section.adviser:
            return True
        return False

class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    fields = ['name','grade_level','class_type','is_adviser','is_subject_teacher','principal_name','school_year']
    template_name = 'sections/section_create.html'
    success_url = reverse_lazy('section-home') 
    
    def form_valid(self, form):
        form.instance.adviser = self.request.user
        return super().form_valid(form)

class SectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Section
    fields = ['name','grade_level','class_type','is_adviser','is_subject_teacher','principal_name','school_year']
    template_name = 'sections/section_update.html'
    
    def form_valid(self, form):
        if form.is_valid():
            messages.success(self.request, f'Section is updated successfully!')
        else:
            messages.error(self.request, f'Section is not updated')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('section-detail', kwargs={'pk': self.kwargs['pk']})

    def get_object(self, queryset=None):
        return get_object_or_404(Section, pk=self.kwargs['pk'])

    def test_func(self):
        section = self.get_object()
        if self.request.user == section.adviser:
            return True
        return False

class SectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Section
    success_url = reverse_lazy('section-home') 
    template_name = "sections/section_confirm_delete.html"

    def post(self, request, *args, **kwargs):
        section = self.get_object()
        print(f"\n\n\n\n{request.POST}")
        if "cancel" in request.POST:
            messages.success(self.request, f'The section {section.name} is not deleted')
            return redirect('section-home')
        else:
            messages.success(self.request, f'The section {section.name} is deleted successfully.')
            return super(SectionDeleteView, self).post(request, *args, **kwargs)
            
    def test_func(self):
        section = self.get_object()
        if self.request.user == section.adviser:
            return True
        return False

class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    fields = ['name','term','order','is_handled_by_owner']
    template_name = 'sections/subject_create.html'
    
    def get_success_url(self):
        base_url = reverse_lazy('section-detail', kwargs={'pk': self.kwargs['pk']})
        return f"{base_url}#listOfSubjects"

    def form_valid(self, form):
        section_id = self.kwargs.get('pk')
        section = get_object_or_404(Section, pk=section_id)
        form.instance.section = section
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    fields = ['name','term','order','is_handled_by_owner']
    template_name = 'sections/subject_update.html'
    
    def get_success_url(self):
        base_url = reverse_lazy('section-detail', kwargs={'pk': self.kwargs['section_pk']})
        return f"{base_url}#listOfSubjects"
    
    def get_object(self, queryset=None):
        return get_object_or_404(Subject, pk=self.kwargs['subject_pk'], section_id=self.kwargs['section_pk'])

    def test_func(self):
        subject = self.get_object()
        if self.request.user == subject.section.adviser:
            return True
        return False

class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        base_url = reverse_lazy('section-detail', kwargs={'pk': self.kwargs['section_pk']})
        return f"{base_url}#listOfSubjects"
    

