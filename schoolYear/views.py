from django.shortcuts import render
from django.views.generic import CreateView
from .models import schoolYear
from django.urls import reverse_lazy
from bootstrap_datepicker_plus.widgets import DatePickerInput

# Create your views here.
class schoolYearCreate(CreateView):
    model = schoolYear
    template_name = 'schoolYear/schoolYear_create.html'
    fields = ['name', 'start_date', 'end_date']
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        return super().form_valid(form)
    
    def get_form(self):
        form = super().get_form()
        form.fields["start_date"].widget = DatePickerInput()
        form.fields["end_date"].widget = DatePickerInput()
        return form