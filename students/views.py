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
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.http import HttpResponse
import csv
from django.contrib.auth.decorators import login_required
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


@login_required
def download_student_template(request, fmt="xlsx"):
    """
    Download the EduAlly student import template.
    fmt = 'xlsx' (default) or 'csv'
    """
    headers = [
        "LRN",
        "Last Name",
        "First Name",
        "Middle Name",
        "Gender",
        "Date of Birth",
    ]
 
    sample_row = [
        "123456789012",
        "Dela Cruz",
        "Juan",
        "Santos",
        "M",
        "2010-05-23",
    ]
 
    if fmt == "csv":
        # ── CSV template ──
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="EduAlly_Student_Import_Template.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerow(sample_row)
        return response
 
    # ── Excel (.xlsx) template ──
    wb = openpyxl.Workbook()
 
    # ── Sheet 1: Instructions ──
    ws_instructions = wb.active
    ws_instructions.title = "Instructions"
    ws_instructions.column_dimensions["A"].width = 80
 
    instructions = [
        ("EduAlly Student Import Template", True, "1a7a4a", 14),
        ("", False, None, 11),
        ("HOW TO USE THIS TEMPLATE", True, "1a7a4a", 11),
        ("1. Go to Sheet 2 (Student Data) to fill in your student list.", False, None, 10),
        ("2. Do NOT rename, delete, or reorder the column headers in Row 1.", False, None, 10),
        ("3. Delete the sample row (Row 2) before uploading.", False, None, 10),
        ("4. Save the file as .xlsx before uploading to EduAlly.", False, None, 10),
        ("", False, None, 10),
        ("COLUMN GUIDE", True, "1a7a4a", 11),
        ("LRN              → 12-digit Learner Reference Number (REQUIRED, must be unique)", False, None, 10),
        ("Last Name        → Student\'s last name (REQUIRED)", False, None, 10),
        ("First Name       → Student\'s first name (REQUIRED)", False, None, 10),
        ("Middle Name      → Optional. Leave blank if none.", False, None, 10),
        ("Gender           → Type M for Male or F for Female only (REQUIRED)", False, None, 10),
        ("Date of Birth    → Format: YYYY-MM-DD  Example: 2010-05-23 (REQUIRED)", False, None, 10),
        ("", False, None, 10),
        ("IMPORTANT NOTES", True, "d94040", 11),
        ("• The system will SKIP students whose LRN is already enrolled in the section.", False, "d94040", 10),
        ("• New student records will be CREATED if the LRN is not yet in your database.", False, "d94040", 10),
        ("• Maximum 500 students per upload. Split into multiple files if needed.", False, "d94040", 10),
        ("• File size limit: 5MB", False, "d94040", 10),
    ]
 
    for row_data in instructions:
        text, bold, color, size = row_data
        cell = ws_instructions.cell(row=ws_instructions.max_row + 1, column=1, value=text)
        cell.font = Font(
            bold=bold,
            color=color or "1a1f2e",
            size=size,
            name="Arial"
        )
        cell.alignment = Alignment(wrap_text=True)
 
    # Lock instructions sheet
    ws_instructions.protection.sheet = True
    ws_instructions.protection.password = "edually"
 
    # ── Sheet 2: Student Data ──
    ws_data = wb.create_sheet(title="Student Data")
 
    # Header styling
    header_fill = PatternFill(
        start_color="1a7a4a",
        end_color="1a7a4a",
        fill_type="solid"
    )
    header_font = Font(
        bold=True,
        color="FFFFFF",
        name="Arial",
        size=10
    )
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
 
    # Write headers
    for col, header in enumerate(headers, start=1):
        cell = ws_data.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
 
    # Write sample row (light gray style)
    sample_fill = PatternFill(
        start_color="f0f0f0",
        end_color="f0f0f0",
        fill_type="solid"
    )
    sample_font = Font(color="888888", name="Arial", size=10, italic=True)
 
    for col, value in enumerate(sample_row, start=1):
        cell = ws_data.cell(row=2, column=col, value=value)
        cell.fill = sample_fill
        cell.font = sample_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="left", vertical="center")
 
    # Add a note above sample row
    ws_data.cell(row=2, column=1).comment = None  # clear any existing
 
    # Column widths
    column_widths = {
        1: 16,   # LRN
        2: 20,   # Last Name
        3: 20,   # First Name
        4: 18,   # Middle Name
        5: 10,   # Gender
        6: 16,   # Date of Birth
    }
    for col, width in column_widths.items():
        ws_data.column_dimensions[
            openpyxl.utils.get_column_letter(col)
        ].width = width
 
    # Freeze header row
    ws_data.freeze_panes = "A2"
 
    # Row 1 height
    ws_data.row_dimensions[1].height = 22
 
    # ── Set Instructions as default active sheet ──
    wb.active = ws_instructions
 
    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )
    response["Content-Disposition"] = ('attachment; filename="EduAlly_Student_Import_Template.xlsx"')
    wb.save(response)
    return response
