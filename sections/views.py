from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Section
from enrollment.models import Enrollment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
        return context

    def test_func(self):
        section = self.get_object()
        if self.request.user == section.adviser:
            return True
        return False

class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    fields = ['name','grade_level','is_adviser','is_subject_teacher','principal_name','school_year']
    template_name = 'sections/section_create.html'
    success_url = reverse_lazy('section-home') 
    
    def form_valid(self, form):
        form.instance.adviser = self.request.user
        return super().form_valid(form)

class SectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Section
    fields = ['name','grade_level','is_adviser','is_subject_teacher','principal_name','school_year']
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

    def test_func(self):
        section = self.get_object()
        if self.request.user == section.adviser:
            return True
        return False
