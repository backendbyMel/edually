from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Section, Subject
from enrollment.models import Enrollment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
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
        context['enrollments'] = Enrollment.objects.filter(
            section=self.get_object()
        )

        context['subjects'] = Subject.objects.filter(
            section=self.object
        ).order_by('order')
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
    fields = ['name','order','is_handled_by_owner']
    template_name = 'sections/subject_create.html'
    
    def get_success_url(self):
        return reverse_lazy('section-detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        section_id = self.kwargs.get('pk')
        section = get_object_or_404(Section, pk=section_id)
        form.instance.section = section
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    fields = ['name','order','is_handled_by_owner']
    template_name = 'sections/subject_create.html'
    
    def get_success_url(self):
        return reverse_lazy('section-detail', kwargs={'pk': self.kwargs['section_pk']})

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
        return reverse_lazy('section-detail', kwargs={'pk': self.kwargs['section_pk']})
    

