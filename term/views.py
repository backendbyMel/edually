from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView
from .models import Term
from schoolYear.models import schoolYear
from bootstrap_datepicker_plus.widgets import DatePickerInput
# Create your views here.
class TermCreate(CreateView):
    model = Term
    template_name = 'term/term_create.html'
    fields = ['name', 'start_date', 'end_date']
    success_url = reverse_lazy('section-home')

    def form_valid(self, form):
        form.instance.school_year = schoolYear.objects.get(is_active=True)
        return super().form_valid(form)
    
    def get_form(self):
        form = super().get_form()
        form.fields["start_date"].widget = DatePickerInput()
        form.fields["end_date"].widget = DatePickerInput()
        return form