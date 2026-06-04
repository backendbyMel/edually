from django.shortcuts import get_object_or_404, redirect, render
from .models import Student, Section, Enrollment
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
        messages.success(request, 'Student is just enrolled')
    else:
        messages.warning(request, 'Student is already enrolled')
    
    return redirect('section-detail', pk=section_pk)