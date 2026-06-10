from datetime import date
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from sections.models import Section, Subject
from attendance.models import Attendance
from term.models import Term
from enrollment.models import Enrollment
from scores.models import Activity
# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm
    return render(request, 'users/register.html', {'form':form})

@login_required
def dashboard(request):
    today = date.today()
    
    # Get all sections of this teacher
    sections = Section.objects.filter(
        adviser=request.user
    )

    alerts = []

    for section in sections:

        # Alert 1: Attendance not recorded today
        today_attendance = Attendance.objects.filter(
            enrollment__section=section,
            date=today
        ).exists()
        if not today_attendance:
            alerts.append({
                'type': 'warning',
                'message': f'Attendance not recorded today for {section.name}',
                'url': reverse('attendance-record', kwargs={'section_pk': section.pk}),
                'priority': 'high'
            })

        # Alert 2: Students below 75
        # Hint: check grades when grade app is ready
        
        # Alert 3: WW below minimum
        subjects = Subject.objects.filter(
            section=section,
            is_handled_by_owner=True
        )
        for subject in subjects:
            try:
                current_term = Term.objects.get(is_current=True)
                ww_count = Activity.objects.filter(
                    subject=subject,
                    term=current_term,
                    component='WW',
                    activity_type='graded'
                ).count()
                if ww_count < 4:
                    alerts.append({
                        'type': 'warning',
                        'message': f'{subject.name} in {section.name} has only {ww_count}/4 Written Works',
                        'url': reverse('activity-list', kwargs={
                            'section_pk': section.pk,
                            'subject_pk': subject.pk
                        }),
                        'priority': 'medium'
                    })
            except Term.DoesNotExist:
                pass

        # Alert 4: At-risk students
        enrollments = Enrollment.objects.filter(
            section=section
        )
        for enrollment in enrollments:
            total = Attendance.objects.filter(
                enrollment=enrollment
            ).count()
            present = Attendance.objects.filter(
                enrollment=enrollment,
                status='P'
            ).count()
            if total > 0:
                percentage = (present / total) * 100
                if percentage < 80:
                    alerts.append({
                        'type': 'danger',
                        'message': f'{enrollment.student.last_name}, {enrollment.student.first_name} in {section.name} is at-risk ({round(percentage, 1)}% attendance)',
                        'url': reverse('student-attendance-detail', kwargs={
                            'section_pk': section.pk,
                            'enrollment_pk': enrollment.pk
                        }),
                        'priority': 'high'
                    })

    return render(request, 'users/dashboard.html', {
        'sections': sections,
        'alerts': alerts,
        'total_sections': sections.count(),
        'total_students': Enrollment.objects.filter(
            section__adviser=request.user
        ).count(),
        'today': today,
        'active_term':current_term,
    })

@login_required
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def coming_soon(request):
    feature_name = request.GET.get('feature', '')
    progress = request.GET.get('progress', 60)
    return render(request, 'users/coming_soon.html', {
        'feature_name': feature_name,
        'progress': progress,
    })

def home(request):
    return render(request, "users/home.html", {"title": "Home"})


