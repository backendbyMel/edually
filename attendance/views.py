from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from sections.models import Section
from enrollment.models import Enrollment
from term.models import Term
from .models import Attendance
from django.urls import reverse
from django.db.models import Count, Q
# Create your views here.
@login_required
def record_attendance(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollments = Enrollment.objects.filter(section=section).select_related('student').order_by(
        'student__last_name',
        'student__gender',)
    
    selected_date = request.GET.get('date', '')
    selected_term = request.GET.get('term', '')
    existing_attendance = {}

    if selected_date:
        attendances = Attendance.objects.filter(
            enrollment__section=section,
            date=selected_date
        )
        # Build lookup dictionary
        # enrollment pk → attendance object
        existing_attendance = {
            a.enrollment.pk: a for a in attendances
        }
    # Step 3: Just render for now
    return render(request, 'attendance/record_attendance.html', {
        'section': section,
        'enrollments': enrollments,
        'existing_attendance': existing_attendance,
        'selected_date': selected_date,
        'selected_term': selected_term,
        'terms': Term.objects.all(),
    })

@login_required
def update_or_create(request, section_pk):
    section =get_object_or_404(Section, pk=section_pk)
    current_term = Term.objects.get(is_active=True)

    created_count = 0
    updated_count = 0

    if request.method == 'POST':
        date = request.POST.get('date')
        enrollments = Enrollment.objects.filter(section=section)
    
        for enrollment in enrollments:
            status = request.POST.get(f'status_{enrollment.pk}')
            remarks = request.POST.get(f'remarks_{enrollment.pk}')
            
            attendance, created = Attendance.objects.update_or_create(
                enrollment=enrollment,
                date=date,
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

                # After loop - show appropriate message
        if created_count > 0 and updated_count == 0:
            messages.success(
                request,
                f'Attendance for {date} has been recorded successfully for {created_count} student(s).'
            )
        elif updated_count > 0 and created_count == 0:
            messages.success(
                request,
                f'Attendance for {date} has been updated successfully for {updated_count} student(s).'
            )
        else:
            messages.success(
                request,
                f'Attendance for {date} has been saved. '
                f'{created_count} new record(s) and {updated_count} record(s) updated.'
            )
            
    base_url = reverse('section-detail', kwargs={'pk': section_pk})
    return redirect(f"{base_url}#attendance")

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
            'term_choices': Term.objects.all(),
        }
    )


@login_required
def student_attendance_history(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollments = Enrollment.objects.filter(section=section).select_related('student').order_by('student__last_name','student__gender')

    # Get filter values
    selected_term = request.GET.get('term', '')

    # Build summary per student
    student_summaries = []

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

        # Compute percentage
        percentage = (present / total * 100) if total > 0 else 0

        # Flag at-risk
        # Hint: research DepEd threshold
        is_at_risk = percentage < 80

        student_summaries.append({
            'enrollment': enrollment,
            'student': enrollment.student,
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'percentage': round(percentage, 2),
            'is_at_risk': is_at_risk,
        })

    return render(
        request,
        'attendance/student_attendance_summary.html',
        {
            'section': section,
            'student_summaries': student_summaries,
            'selected_term': selected_term,
            'terms': Term.objects.all(),
        }
    )

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
    total = attendances.count()
    present = attendances.filter(status='P').count()
    absent = attendances.filter(status='A').count()
    late = attendances.filter(status='L').count()
    excused = attendances.filter(status='E').count()
    percentage = round(
        present / total * 100, 2
    ) if total > 0 else 0
    is_at_risk = percentage < 80

    return render(
        request,
        'attendance/student_attendance_detail.html',
        {
            'section': section,
            'enrollment': enrollment,
            'attendances': attendances,
            'selected_term': selected_term,
            'terms': Term.objects.all(),
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'percentage': percentage,
            'is_at_risk': is_at_risk,
        }
    )

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