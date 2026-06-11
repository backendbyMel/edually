from datetime import date
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import UserRegisterForm, EmailChangeForm, NameChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from sections.models import Section, Subject
from attendance.models import Attendance
from term.models import Term
from enrollment.models import Enrollment
from scores.models import Activity
from django.contrib.auth.models import User
from django.core.mail import send_mail
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
    current_term = Term.objects.filter(is_current=True).first()
    if sections:
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

@login_required
def change_email(request):
    if request.method == 'POST':
        new_email = request.POST.get('email', '').strip()

        # Validate email
        if not new_email:
            messages.error(request, 'Email cannot be empty.')
            return redirect('change-email')

        # Check if email already used by another user
        from django.contrib.auth.models import User
        if User.objects.filter(
            email=new_email
        ).exclude(pk=request.user.pk).exists():
            messages.error(
                request,
                'This email is already used by another account.'
            )
            return redirect('change-email')

        # Save new email
        request.user.email = new_email
        request.user.save()
        messages.success(
            request,
            'Your email has been updated successfully.'
        )
        return redirect('profile')

    return render(
        request,
        'users/change_email.html',
        {'current_email': request.user.email}
    )


def forgot_username(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            try:
                user = User.objects.get(email=email)

                send_mail(
                    subject='EduAlly — Your Username',
                    message=f'''Hello {user.first_name},

                        You requested your username for EduAlly.

                        Your username is: {user.username}

                        You can log in at: {request.build_absolute_uri('/login/')}

                        If you did not request this, please ignore this email.

                        — EduAlly Team''',
                    from_email='EduAlly <your_email@gmail.com>',
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(
                    request,
                    'Your username has been sent to your email.'
                )

            except User.DoesNotExist:
                # Do not reveal if email exists or not
                # for security reasons
                messages.success(
                    request,
                    'If that email is registered, '
                    'your username has been sent.'
                )

        return redirect('forgot-username')

    return render(request, 'users/forgot_username.html')


@login_required
def change_email(request):
    if request.method == "POST":
        form = EmailChangeForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your email address has been updated.")
            return redirect("profile")
    else:
        form = EmailChangeForm(instance=request.user)

    return render(request, "users/email_change.html", {"form": form})


@login_required
def change_name(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        form = NameChangeForm(request.POST)

        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()

            profile.middle_name = form.cleaned_data["middle_name"]
            profile.save()

            messages.success(request, "Your name has been updated.")
            return redirect("profile")
    else:
        form = NameChangeForm(initial={
            "first_name": user.first_name,
            "middle_name": profile.middle_name,
            "last_name": user.last_name,
        })

    return render(request, "users/name_change.html", {"form": form})