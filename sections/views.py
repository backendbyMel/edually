from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Section, Subject
from enrollment.models import Enrollment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from attendance.models import Attendance
import datetime
from attendance.views import get_term_months
from term.models import Term
from attendance.views import calculate_school_days
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
import os
from django.conf import settings
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
# Create your views here.
class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'sections/section_home.html'
    context_object_name = 'sections'
    paginate_by = 8

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
    fields = ['name','grade_level','class_type','is_adviser','is_subject_teacher','school_name','school_id','region','division','principal_name','school_year']
    template_name = 'sections/section_create.html'
    success_url = reverse_lazy('section-home') 
    
    def form_valid(self, form):
        form.instance.adviser = self.request.user
        return super().form_valid(form)

class SectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Section
    fields = ['name','grade_level','class_type','is_adviser','is_subject_teacher','school_name','school_id','region','division','principal_name','school_year']
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
    fields = ['name','subject_type','term','order','is_handled_by_owner']
    template_name = 'sections/subject_create.html'
    
    def get_success_url(self):
        base_url = reverse_lazy('section-detail', kwargs={'pk': self.kwargs['pk']})
        return f"{base_url}#listOfSubjects"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        section = get_object_or_404(
            Section,
            pk=self.kwargs['pk']
        )

        if section.class_type == 'JHS':
            form.fields['subject_type'].choices = [
                ('jhs_regular', 'JHS - Regular Subject'),
                ('jhs_tle_mapeh', 'JHS - TLE / MAPEH'),
            ]
        elif section.class_type == 'SHS':
            form.fields['subject_type'].choices = [
                ('core', 'SHS - Core'),
                ('academic_elective', 'SHS - Academic Elective - All Other'),
                ('academic_field', 'SHS - Academic Elective - Field/Exposure/Sports/Arts'),
                ('techpro_elective', 'SHS - TechPro Elective - All Other'),
                ('techpro_immersion', 'SHS - TechPro Elective - Work Immersion'),
            ]

        return form
    
    def form_valid(self, form):
        section_id = self.kwargs.get('pk')
        section = get_object_or_404(Section, pk=section_id)
        form.instance.section = section
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    fields = ['name','subject_type','term','order','is_handled_by_owner']
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

class SectionMasterlistDocxView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_section(self):
        return get_object_or_404(Section, pk=self.kwargs['pk'])

    def set_single_spacing(self, paragraph):
        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        
    def test_func(self):
        section = self.get_section()
        return self.request.user == section.adviser

    def format_student_name(self, student):
        middle_initial = ''
        if student.middle_name:
            middle_initial = f' {student.middle_name[0].upper()}.'

        return f'{student.last_name}, {student.first_name}{middle_initial}'.upper()

    def add_student_table(self, cell, title, enrollments):
        title_paragraph = cell.paragraphs[0]
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_paragraph.add_run(title)
        title_run.bold = True
        title_run.font.size = Pt(10)

        table = cell.add_table(rows=1, cols=3)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        header = table.rows[0].cells
        header[0].text = 'No.'
        header[1].text = 'LRN'
        header[2].text = 'Name'

        for header_cell in header:
            for paragraph in header_cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(8)

        for number, enrollment in enumerate(enrollments, start=1):
            student = enrollment.student

            row = table.add_row().cells
            row[0].text = str(number)
            row[1].text = str(student.lrn or '')
            row[2].text = self.format_student_name(student)

            row[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            for row_cell in row:
                for paragraph in row_cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(8)

    def get(self, request, *args, **kwargs):
        section = self.get_section()

        male_enrollments = Enrollment.objects.filter(
            section=section,
            student__gender__iexact='M'
        ).select_related('student').order_by(
            'student__last_name',
            'student__first_name'
        )

        female_enrollments = Enrollment.objects.filter(
            section=section,
            student__gender__iexact='F'
        ).select_related('student').order_by(
            'student__last_name',
            'student__first_name'
        )

        document = Document()

        doc_section = document.sections[0]
        doc_section.top_margin = Inches(0.4)
        doc_section.bottom_margin = Inches(0.4)
        doc_section.left_margin = Inches(0.4)
        doc_section.right_margin = Inches(0.4)

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'deped_logo.png')

        if os.path.exists(logo_path):
            logo = document.add_paragraph()
            logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_run = logo.add_run()
            logo_run.add_picture(logo_path, width=Inches(0.65))

        p = document.add_paragraph()
        self.set_single_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run('Republic of the Philippines')
        run.font.name = 'Old English Text MT'
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(110, 110, 110)

        p = document.add_paragraph()
        self.set_single_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run('Department of Education')
        run.font.name = 'Old English Text MT'
        run.font.size = Pt(18)
        run.bold = True
        run.font.color.rgb = RGBColor(110, 110, 110)

        header_lines = [
            'Region ' + section.region or 'Region X- Northern Mindanao',
            'Schools Division of ' + section.division or 'Schools Division of Cagayan de Oro',
            section.school_name or 'Lumbia National High School',
            'Ysalina Street, Lumbia, Cagayan de Oro City',
        ]

        for line in header_lines:
            p = document.add_paragraph()
            self.set_single_spacing(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line)
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(90, 90, 90)

        # horizontal line
        line_table = document.add_table(rows=1, cols=1)
        line_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        line_cell = line_table.cell(0, 0)
        line_cell.text = ''
        tc_pr = line_cell._tc.get_or_add_tcPr()
        tc_borders = OxmlElement('w:tcBorders')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '8')
        bottom.set(qn('w:space'), '0')
        bottom.set(qn('w:color'), '000000')
        tc_borders.append(bottom)
        tc_pr.append(tc_borders)

        p = document.add_paragraph()
        self.set_single_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run('LIST OF LEARNERS')
        run.bold = True
        run.font.size = Pt(12)

        p = document.add_paragraph()
        self.set_single_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f'GRADE {section.grade_level} - {section.name}')
        run.bold = True
        run.font.size = Pt(12)

        p = document.add_paragraph()
        self.set_single_spacing(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f'{section.school_year}')
        run.bold = True
        run.font.size = Pt(11)

        document.add_paragraph()

        outer_table = document.add_table(rows=1, cols=2)
        outer_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        male_cell = outer_table.rows[0].cells[0]
        female_cell = outer_table.rows[0].cells[1]

        self.add_student_table(male_cell, 'MALE', male_enrollments)
        self.add_student_table(female_cell, 'FEMALE', female_enrollments)

        document.add_paragraph()
        document.add_paragraph()

        teacher_name = request.user.get_full_name() or request.user.username

        teacher = document.add_paragraph()
        teacher.alignment = WD_ALIGN_PARAGRAPH.CENTER
        teacher_run = teacher.add_run(teacher_name.upper())
        teacher_run.bold = True
        teacher_run.font.size = Pt(10)

        label = document.add_paragraph()
        label.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label.add_run('Teacher')

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{section.name}_masterlist.docx"'
        )

        document.save(response)
        return response

