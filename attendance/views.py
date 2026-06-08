from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from sections.models import Section
from enrollment.models import Enrollment
from term.models import Term
from .models import Attendance
from django.urls import reverse
from django.db.models import Count, Q
import os
import calendar
from datetime import date, timedelta, datetime
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from schoolYear.models import schoolYear
# Create your views here.

#create attendance
@login_required
def record_attendance(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollments = Enrollment.objects.filter(section=section).select_related('student').order_by(
        'student__last_name',
        'student__gender',)
    
    selected_date = request.GET.get('date', '')
    selected_term = request.GET.get('term', '')
    existing_attendance = {}
    
    

    if enrollments:
        if selected_date:
            attendances = Attendance.objects.filter(
                enrollment__section=section,
                date=selected_date
            )
            
            existing_attendance = {
                a.enrollment.pk: a for a in attendances
            }
    else:
        messages.error(request, "Cannot record attendance. There are no students currently enrolled in this section")
        return redirect(reverse('section-detail', kwargs={'pk': section_pk}) + '#attendance')
    
    return render(request, 'attendance/record_attendance.html', {
        'section': section,
        'enrollments': enrollments,
        'existing_attendance': existing_attendance,
        'selected_date': selected_date,
        'selected_term': selected_term,
        'terms': Term.objects.all(),
    })

#update or create a data to database
@login_required
def update_or_create(request, section_pk):
    section =get_object_or_404(Section, pk=section_pk)
    current_term = Term.objects.get(is_current=True)

    created_count = 0
    updated_count = 0

    if request.method == 'POST':
        date_str = request.POST.get('date')
        enrollments = Enrollment.objects.filter(section=section)
    
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date format.')
            return redirect(reverse('section-detail', kwargs={'pk': section_pk}) + '#attendance')
        if not (current_term.start_date <= attendance_date <= current_term.end_date):
            messages.error(
                request,
                f'{attendance_date.strftime("%B %d, %Y")} is outside the active term '
                f'({current_term.name}: {current_term.start_date.strftime("%B %d, %Y")} '
                f'— {current_term.end_date.strftime("%B %d, %Y")}). '
                f'Attendance was not saved.'
            )
            return redirect(reverse('section-detail', kwargs={'pk': section_pk}) + '#attendance')
        
        if attendance_date.weekday() >= 5:
            messages.error(
                request,
                f'{attendance_date.strftime("%B %d, %Y")} is a weekend. '
                f'Attendance was not saved.'
            )
            return redirect(reverse('section-detail', kwargs={'pk': section_pk}) + '#attendance')
        
        for enrollment in enrollments:
            status = request.POST.get(f'status_{enrollment.pk}')
            remarks = request.POST.get(f'remarks_{enrollment.pk}')
            
            attendance, created = Attendance.objects.update_or_create(
                enrollment=enrollment,
                date=attendance_date,
                term=current_term,
                defaults={
                    'status': status,
                    'remarks': remarks,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        
        if created_count > 0 and updated_count == 0:
            messages.success(
                request,
                f'Attendance for {attendance_date.strftime("%B %d, %Y")} has been recorded '
                f'successfully for {created_count} student(s).'
            )
        elif updated_count > 0 and created_count == 0:
            messages.success(
                request,
                f'Attendance for {attendance_date.strftime("%B %d, %Y")} has been updated '
                f'successfully for {updated_count} student(s).'
            )
        else:
            messages.success(
                request,
                f'Attendance for {attendance_date.strftime("%B %d, %Y")} has been saved. '
                f'{created_count} new record(s) and {updated_count} record(s) updated.'
            )
            
    base_url = reverse('section-detail', kwargs={'pk': section_pk})
    return redirect(f"{base_url}#attendance")

#summary by date
@login_required
def attendance_history(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)

    # Get filter values
    selected_term = request.GET.get('term', '')
    selected_date = request.GET.get('date', '')

    # Base queryset
    attendances = Attendance.objects.filter(
        enrollment__section=section
    )

    # Apply filters
    if selected_term:
        attendances = attendances.filter(term=selected_term)

    if selected_date:
        attendances = attendances.filter(date=selected_date)

    # Group by date with gender breakdown
    daily_summary = attendances.values('date', 'term').annotate(
        present_male=Count('id', filter=Q(
            status='P',
            enrollment__student__gender='M'
        )),
        present_female=Count('id', filter=Q(
            status='P',
            enrollment__student__gender='F'
        )),
        absent=Count('id', filter=Q(status='A')),
        late=Count('id', filter=Q(status='L')),
        excused=Count('id', filter=Q(status='E')),
        total=Count('id'),
    ).order_by('date')

    return render(
        request,
        'attendance/summary_attendance.html',
        {
            'section': section,
            'daily_summary': daily_summary,
            'selected_term': selected_term,
            'selected_date': selected_date,
            'term_choices': Term.objects.all().order_by('name'),
        }
    )

@login_required
def delete_attendance_by_date(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        term = request.POST.get('term')

        deleted_count, _ = Attendance.objects.filter(
            enrollment__section=section,
            date=date,
            term=term
        ).delete()

        messages.success(request, f'Attendance records for {date} ({term}) deleted successfully. ({deleted_count} records removed)')
    
    return redirect('attendance-summary', section_pk=section_pk)

def calculate_school_days(start_date, end_date):
    total_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:
            total_days += 1
        current_date += timedelta(days=1)
    return total_days

#summary by student
@login_required
def student_attendance_history(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollments = Enrollment.objects.filter(section=section).select_related('student').order_by('student__last_name','student__gender')

    # Get filter values
    selected_term = request.GET.get('term', '')
    show_at_risk = request.GET.get('at_risk', '') == 'true'

    # Build summary per student
    student_summaries = []

    total_school_days = 0
    if selected_term:
        # Get the specific term dates
        term_obj = get_object_or_404(Term, pk=selected_term)
        total_school_days = calculate_school_days(term_obj.start_date, term_obj.end_date)
    else:
        total_school_days = 0
        for term_obj in Term.objects.all():
            total_school_days += calculate_school_days(term_obj.start_date, term_obj.end_date)

    
    for enrollment in enrollments:

        # Base queryset for this student
        attendances = Attendance.objects.filter(
            enrollment=enrollment
        )

        
        # Apply term filter if selected
        if selected_term:
            attendances = attendances.filter(
                term=selected_term
            )

        # Count each status
        
        total = attendances.count()
        present = attendances.filter(status='P').count()
        absent = attendances.filter(status='A').count()
        late = attendances.filter(status='L').count()
        excused = attendances.filter(status='E').count()

        attendance_rate = (present / total * 100) if total > 0 else 0

        # Absence rate (absent / total) — DepEd threshold is 20% max allowable absences
        absence_rate = (absent / total_school_days * 100) if total_school_days > 0 else 0

        # At-risk if absences exceed 20% of total school days
        is_at_risk = absence_rate > 20

        student_summaries.append({
            'enrollment': enrollment,
            'student': enrollment.student,
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'attendance_rate': round(attendance_rate, 2),  # renamed for clarity
            'absence_rate': round(absence_rate, 2),         # new
            'is_at_risk': is_at_risk,
        })

    if show_at_risk:
        student_summaries = [s for s in student_summaries if s['is_at_risk']]

    return render(
        request,
        'attendance/student_attendance_summary.html',
        {
            'section': section,
            'student_summaries': student_summaries,
            'selected_term': selected_term,
            'terms': Term.objects.all().order_by('name'),
        }
    )

#attendance detail per student
@login_required
def student_attendance_detail(request, section_pk, enrollment_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)

    # Get filter values
    selected_term = request.GET.get('term', '')

    # Get all attendance for this specific student
    attendances = Attendance.objects.filter(
        enrollment=enrollment
    )

    # Apply term filter
    if selected_term:
        attendances = attendances.filter(term=selected_term)

    # Order by date
    attendances = attendances.order_by('date')

    total_school_days = 0
    if selected_term:
        # Get the specific term dates
        term_obj = get_object_or_404(Term, pk=selected_term)
        total_school_days = calculate_school_days(term_obj.start_date, term_obj.end_date)
    else:
        total_school_days = 0
        for term_obj in Term.objects.all():
            total_school_days += calculate_school_days(term_obj.start_date, term_obj.end_date)
    
    total = attendances.count()
    present = attendances.filter(status='P').count()
    absent = attendances.filter(status='A').count()
    late = attendances.filter(status='L').count()
    excused = attendances.filter(status='E').count()
    percentage = round(
        present / total_school_days * 100, 2
    ) if total_school_days > 0 else 0

    attendance_rate = (present / total_school_days * 100) if total_school_days > 0 else 0
    absence_rate = (absent / total_school_days * 100) if total_school_days > 0 else 0

    # At-risk if absences exceed 20% of total school days
    is_at_risk = absence_rate > 20
    print(f"\n\n\nHEY I AM HERE.\n\n\n{is_at_risk}\n\n\n")
    # is_at_risk = percentage > 20

    return render(
        request,
        'attendance/student_attendance_detail.html',
        {
            'section': section,
            'enrollment': enrollment,
            'attendances': attendances,
            'selected_term': selected_term,
            'terms': Term.objects.all().order_by('name'),
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'percentage': percentage,
            'is_at_risk': is_at_risk,
        }
    )

#edit student attendance
@login_required
def student_attendance_edit(request, section_pk, attendance_pk):
    section = get_object_or_404(Section, pk=section_pk)
    attendance = get_object_or_404(Attendance, pk=attendance_pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')

        # Update the specific attendance record
        attendance.status = status
        attendance.remarks = remarks
        attendance.save()  # hint: what method saves a model object?

        messages.success(request, f'Attendance is saved successfully')
        return redirect(reverse('attendance-student-detail', kwargs={
                'section_pk': section_pk, 
                'enrollment_pk': attendance.enrollment.id
            }))

    return render(request, 'attendance/student_attendance_edit.html', {
        'section': section,
        'attendance': attendance,
    })

MONTH_NAMES = {
    1: "JANUARY", 2: "FEBRUARY", 3: "MARCH", 4: "APRIL",
    5: "MAY", 6: "JUNE", 7: "JULY", 8: "AUGUST",
    9: "SEPTEMBER", 10: "OCTOBER", 11: "NOVEMBER", 12: "DECEMBER",
}

DAY_LETTERS = ['M', 'T', 'W', 'TH', 'F']
 
TEMPLATE_PATH = os.path.join(
    settings.BASE_DIR,
    'attendance',
    'templates_xlsx',
    'sf2_template.xlsx'
)
def get_active_school_year():
    """Get the currently active school year."""
    return schoolYear.objects.filter(is_active=True).first()

def get_term_months():
    """Return list of (month_num, month_name) covered across all terms."""
    school_year = get_active_school_year()
    if not school_year:
        return []

    terms = Term.objects.filter(
        school_year=school_year,
    ).order_by('start_date')

    if not terms.exists():
        return []

    months = []
    seen = set()
    for term in terms:
        current = date(term.start_date.year, term.start_date.month, 1)
        end     = date(term.end_date.year, term.end_date.month, 1)
        while current <= end:
            key = (current.year, current.month)
            if key not in seen:
                seen.add(key)
                months.append({
                    'num':   current.month,
                    'year':  current.year,
                    'label': f"{current.strftime('%B')} {current.year}",
                })
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
    return months

def get_school_days(year: int, month: int) -> list:
    """All weekdays (Mon–Fri) for a given month."""
    school_year = get_active_school_year()
    if not school_year:
        return []

    terms = Term.objects.filter(
        school_year=school_year,
    ).order_by('start_date')

    month_start = date(year, month, 1)
    month_end   = date(year, month, calendar.monthrange(year, month)[1])

    days = []
    for day_num in range(1, calendar.monthrange(year, month)[1] + 1):
        d = date(year, month, day_num)
        if d.weekday() >= 5:   # skip weekends
            continue
        # Only include days that fall within at least one term's range
        for term in terms:
            if term.start_date <= d <= term.end_date:
                days.append(d)
                break

    return days
 
def check_missing_attendance(section, year: int, month: int) -> list:
    enrollments = Enrollment.objects.filter(section=section)
    if not enrollments.exists():
        return []

    school_days = get_school_days(year, month)
    if not school_days:
        return []

    print("\n\n\nSchool days:", school_days)

    # Use the latest recorded date as the boundary instead of today
    # This handles cases where attendance is recorded ahead of the server date
    latest_recorded = Attendance.objects.filter(
        enrollment__in=enrollments,
        date__in=school_days,
    ).order_by('-date').values_list('date', flat=True).first()

    if not latest_recorded:
        return [
            f"No attendance has been recorded yet for this month. "
            f"Please record attendance before downloading SF2."
        ]

    # Check all school days up to and including the latest recorded date
    days_to_check = [d for d in school_days if d <= latest_recorded]

    enrolled_ids = set(enrollments.values_list('pk', flat=True))

    missing = []
    for d in days_to_check:
        recorded_ids = set(
            Attendance.objects.filter(
                enrollment__in=enrollments,
                date=d,
            ).values_list('enrollment_id', flat=True)
        )
        unrecorded = enrolled_ids - recorded_ids
        if unrecorded:
            missing.append(
                f"{d.strftime('%B %d, %Y (%A)')} — "
                f"{len(unrecorded)} student(s) missing"
            )

    return missing
 
@login_required
def generate_sf2(request, section_pk: int, month: int, year: int):
    section = get_object_or_404(Section, pk=section_pk)

    is_adviser = hasattr(section, 'adviser') and section.adviser == request.user
    if not (is_adviser or request.user.is_superuser):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    school_year_obj = get_active_school_year()
    if not school_year_obj:
        messages.error(request, "No active school year found. Please set one in the admin.")
        return redirect(reverse('section-detail', kwargs={'pk': section_pk}) + '#attendance')

    # Check missing attendance BEFORE doing anything else
    missing_dates = check_missing_attendance(section, year, month)
    confirmed = request.GET.get('confirm') == 'yes'
    if missing_dates and not confirmed:
        return render(request, 'attendance/sf2_confirm_download.html', {
            'section':      section,
            'missing_dates': missing_dates,
            'month_label':  f"{month_name} {year}",
            'confirm_url':  request.path + '?confirm=yes',
        })

    # ── Data preparation ───────────────────────────────────────────────────
    school_days = get_school_days(year, month)
    month_name  = MONTH_NAMES.get(month, "")

    enrollments = (
        Enrollment.objects
        .filter(section=section)
        .select_related('student')
        .order_by('student__last_name', 'student__first_name')
    )
    males   = [e for e in enrollments if e.student.gender == 'M']
    females = [e for e in enrollments if e.student.gender == 'F']

    # Build att_map keyed by (enrollment_id, date_isoformat)
    all_att = Attendance.objects.filter(
        enrollment__in=enrollments,
        date__in=school_days,        # only valid term school days
    ).values('enrollment_id', 'date', 'status')
    
    att_map = {}
    for row in all_att:
        att_map.setdefault(row['enrollment_id'], {})[row['date'].isoformat()] = row['status']

    # ── Fill template ──────────────────────────────────────────────────────
    wb = load_workbook(TEMPLATE_PATH)
    ws = wb.active

    ws['G6']  = "0000000"               # replace with school_id from your model
    ws['N6']  = school_year_obj.name
    ws['AA6'] = month_name
    ws['G7']  = "YOUR SCHOOL NAME"      # replace with school name from your model
    ws['AA7'] = section.grade_level
    ws['AF7'] = section.name
    ws['AQ9'] = len(school_days)

    DATE_START_COL = 7
    print("\n\nSchool days:", school_days)
    print("DATE_START_COL:", DATE_START_COL)
    for i, d in enumerate(school_days[:25]):
        ws.cell(row=10, column=DATE_START_COL + i).value = d.day
        ws.cell(row=11, column=DATE_START_COL + i).value = DAY_LETTERS[d.weekday()]
        print(f"  Day {d} → col {DATE_START_COL + i}")
    # Clear leftover date columns beyond actual school days
    for i in range(len(school_days), 25):
        ws.cell(row=10, column=DATE_START_COL + i).value = None
        ws.cell(row=11, column=DATE_START_COL + i).value = None

    def fill_students(student_enrollments, start_row):
        for idx, enrollment in enumerate(student_enrollments[:50]):
            row  = start_row + idx
            stu  = enrollment.student
            name = f"{stu.last_name}, {stu.first_name}"
            if hasattr(stu, 'middle_name') and stu.middle_name:
                name += f" {stu.middle_name[0]}."

            ws.cell(row=row, column=1).value = idx + 1
            ws.cell(row=row, column=2).value = name

            daily = att_map.get(enrollment.pk, {})
            print(f"\n\n\nEnrollment {enrollment.pk}: {daily}")

            for i, d in enumerate(school_days[:25]):
                status = daily.get(d.isoformat())
                if status == 'A':
                    cell_val = 'A'
                elif status == 'L':
                    cell_val = 'L'
                elif status in ('P', 'E'):
                    cell_val = 'P'      
                else:
                    cell_val = '?'     # missing record — visible indicator

                ws.cell(row=row, column=DATE_START_COL + i).value = cell_val

        # Clear unused student rows
        for idx in range(len(student_enrollments), 50):
            row = start_row + idx
            ws.cell(row=row, column=1).value = None
            ws.cell(row=row, column=2).value = None
            for i in range(25):
                ws.cell(row=row, column=DATE_START_COL + i).value = None

    fill_students(males,   start_row=13)
    fill_students(females, start_row=64)

    ws['AK119'] = len(males)
    ws['AL119'] = len(females)
    ws['AK143'] = request.user.get_full_name() or request.user.username

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"SF2_{section.name}_{month_name}_{year}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response