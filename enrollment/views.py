from django.shortcuts import get_object_or_404, redirect, render
from .models import Student, Section, Enrollment
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
# Create your views here.

@login_required
def search_student(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    query = request.GET.get('student_name', '').strip()
    results = []

    if query:
        results = Student.objects.filter(
            Q(lrn__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).filter(added_by=request.user).order_by('last_name', 'first_name')

    return render(request, 'enrollment/search_results.html', {
        'section': section,
        'results': results,
        'query': query,
    })

@login_required
def enroll_student(request, section_pk, student_pk):
    section = get_object_or_404(Section, pk=section_pk)
    student = get_object_or_404(Student, pk=student_pk)

    enrollment, created = Enrollment.objects.get_or_create(
        section=section,
        student=student,
        added_by=request.user
    )
    if created:
        messages.success(request, f'Student {enrollment.student.lrn} is enrolled successfully')
    else:
        messages.warning(request, f'Student {enrollment.student.lrn} is already enrolled')
    
    base_url = reverse('section-detail', kwargs={'pk': section_pk})
    return redirect(f"{base_url}#enrolledStudents")

@login_required
def enroll_delete(request, section_pk, enrollment_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk, section=section, added_by=request.user)
    enrollment_delete = enrollment.delete()
    if enrollment_delete:
        messages.success(request, f'Student {enrollment.student.lrn} is unenrolled from the section {enrollment.section.name} successfully')
    base_url = reverse('section-detail', kwargs={'pk': section_pk})
    return redirect(f"{base_url}#enrolledStudents")
