from django.shortcuts import redirect, render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Activity, Score
from sections.models import Subject, Section
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from enrollment.models import Enrollment
from term.models import Term
# Create your views here.
class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = 'scores/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 10
    
    def get_queryset(self):
        self.subject = get_object_or_404(Subject, pk=self.kwargs['subject_pk'])
        return Activity.objects.filter(subject=self.subject).order_by('term', 'component', 'date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = get_object_or_404(Section, pk=self.kwargs['section_pk'])
        subject = get_object_or_404(Subject, pk=self.kwargs['subject_pk'])

        # Get active term
        from term.models import Term
        try:
            current_term = Term.objects.get(is_current=True)
        except Term.DoesNotExist:
            current_term = None

        # Count WW and PT for current term
        # Hint: for DepEd minimum alert
        if current_term:
            ww_count = Activity.objects.filter(
                subject=subject,
                term=current_term,
                component='WW',
                activity_type='graded'
            ).count()

            pt_count = Activity.objects.filter(
                subject=subject,
                term=current_term,
                component='PT',
                activity_type='graded'
            ).count()
            qa_count = Activity.objects.filter(
                subject=subject,
                term=current_term,
                component='TE',
                activity_type='graded'
            ).count()
        else:
            ww_count = 0
            pt_count = 0
            qa_count = 0

        context['section'] = section
        context['subject'] = subject
        context['current_term'] = current_term
        context['ww_count'] = ww_count
        context['pt_count'] = pt_count
        context['ww_alert'] = ww_count < 4
        context['pt_alert'] = pt_count < 4
        context['qa_count'] = qa_count
        return context

class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    template_name = 'scores/activity_create.html'
    fields = [
        'title',
        'description',
        'activity_type',
        'component',
        'total_score',
        'date'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = get_object_or_404(
            Section,
            pk=self.kwargs['section_pk']
        )
        context['subject'] = get_object_or_404(
            Subject,
            pk=self.kwargs['subject_pk']
        )
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Make component and total_score optional
        # since they are only needed for graded activities
        form.fields['component'].required = False
        form.fields['total_score'].required = False

        # Add Bootstrap classes
        for field_name, field in form.fields.items():
            if hasattr(field.widget, 'choices'):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

        return form

    def form_valid(self, form):
        subject = get_object_or_404(
            Subject,
            pk=self.kwargs['subject_pk']
        )
        # Get active term automatically
        
        try:
            current_term = Term.objects.get(is_current=True)
        except Term.DoesNotExist:
            messages.warning(
                self.request,
                'No active term found. Please set an active term first.'
            )
            return self.form_invalid(form)

        form.instance.subject = subject
        form.instance.term = current_term
        messages.success(
            self.request,
            f'Activity "{form.instance.title}" created successfully.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        base_url = reverse(
            'activity-list',
            kwargs={
                'section_pk': self.kwargs['section_pk'],
                'subject_pk': self.kwargs['subject_pk']
            }
        )
        return base_url
    
class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    template_name = 'scores/activity_create.html'
    fields = [
        'title',
        'description',
        'activity_type',
        'component',
        'total_score',
        'date'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = get_object_or_404(
            Section,
            pk=self.kwargs['section_pk']
        )
        context['subject'] = get_object_or_404(
            Subject,
            pk=self.kwargs['subject_pk']
        )
        context['is_update'] = True
        return context

    def get_success_url(self):
        messages.success(
            self.request,
            f'Activity updated successfully.'
        )
        return reverse(
            'activity-list',
            kwargs={
                'section_pk': self.kwargs['section_pk'],
                'subject_pk': self.kwargs['subject_pk']
            }
        )

class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity

    def get(self, request, *args, **kwargs):
        # Delete immediately without confirmation page
        # Hint: use modal in template instead
        self.object = self.get_object()
        section_pk = self.kwargs['section_pk']
        subject_pk = self.kwargs['subject_pk']
        activity_title = self.object.title
        self.object.delete()
        messages.success(
            request,
            f'Activity "{activity_title}" deleted successfully.'
        )
        return redirect(
            'activity-list',
            section_pk=section_pk,
            subject_pk=subject_pk
        )

    def get_success_url(self):
        return reverse(
            'activity-list',
            kwargs={
                'section_pk': self.kwargs['section_pk'],
                'subject_pk': self.kwargs['subject_pk']
            }
        )

@login_required
def score_input(request, section_pk, subject_pk, activity_pk):
    section = get_object_or_404(Section, pk=section_pk)
    subject = get_object_or_404(Subject, pk=subject_pk)
    activity = get_object_or_404(Activity, pk=activity_pk)

    # Get all enrollments for this section
    enrollments = Enrollment.objects.filter(
        section=section
    ).select_related('student').order_by(
        'student__gender',
        'student__last_name'
    )

    # Get existing scores for pre-population
    existing_scores = Score.objects.filter(
        activity=activity
    )
    # Build lookup dictionary
    score_map = {
        s.enrollment.pk: s for s in existing_scores
    }

    if request.method == 'POST':
        saved_count = 0

        for enrollment in enrollments:
            # Handle differently based on activity type
            if activity.activity_type == 'graded':
                score_value = request.POST.get(
                    f'score_{enrollment.pk}'
                )
                remarks = request.POST.get(
                    f'remarks_{enrollment.pk}', ''
                )

                # Validate score does not exceed total
                if score_value:
                    try:
                        score_float = float(score_value)
                        if score_float > activity.total_score:
                            messages.error(
                                request,
                                f'Score for {enrollment.student} '
                                f'exceeds total score of '
                                f'{activity.total_score}.'
                            )
                            return redirect(
                                'score-input',
                                section_pk=section_pk,
                                subject_pk=subject_pk,
                                activity_pk=activity_pk
                            )
                    except ValueError:
                        pass

                Score.objects.update_or_create(
                    activity=activity,
                    enrollment=enrollment,
                    defaults={
                        'score': score_value or None,
                        'remarks': remarks,
                    }
                )

            elif activity.activity_type == 'compliance':
                is_complied = request.POST.get(
                    f'complied_{enrollment.pk}'
                )
                remarks = request.POST.get(
                    f'remarks_{enrollment.pk}', ''
                )
                Score.objects.update_or_create(
                    activity=activity,
                    enrollment=enrollment,
                    defaults={
                        'is_complied': is_complied == 'yes',
                        'remarks': remarks,
                    }
                )

            elif activity.activity_type == 'recorded':
                remarks = request.POST.get(
                    f'remarks_{enrollment.pk}', ''
                )
                Score.objects.update_or_create(
                    activity=activity,
                    enrollment=enrollment,
                    defaults={
                        'remarks': remarks,
                    }
                )

            saved_count += 1

        messages.success(
            request,
            f'Scores saved for {saved_count} student(s).'
        )
        return redirect(
            'activity-list',
            section_pk=section_pk,
            subject_pk=subject_pk
        )

    return render(request, 'scores/score_input.html', {
        'section': section,
        'subject': subject,
        'activity': activity,
        'enrollments': enrollments,
        'score_map': score_map,
    })

@login_required
def score_view(request, section_pk, subject_pk, activity_pk):
    section = get_object_or_404(Section, pk=section_pk)
    subject = get_object_or_404(Subject, pk=subject_pk)
    activity = get_object_or_404(Activity, pk=activity_pk)

    enrollments = Enrollment.objects.filter(
        section=section
    ).select_related('student').order_by(
        'student__gender',
        'student__last_name'
    )

    # Get all scores for this activity
    scores = Score.objects.filter(
        activity=activity
    )

    # Build lookup dictionary
    score_map = {
        s.enrollment.pk: s for s in scores
    }

    # Compute summary stats for graded activities
    if activity.activity_type == 'graded':
        scored_students = scores.exclude(
            score=None
        )
        total_scored = scored_students.count()
        
        if total_scored > 0:
            score_values = [
                float(s.score) for s in scored_students
            ]
            highest = max(score_values)
            lowest = min(score_values)
            average = sum(score_values) / total_scored
            passing = scored_students.filter(
                score__gte=activity.total_score * 0.75
            ).count()
        else:
            highest = lowest = average = passing = 0
    else:
        highest = lowest = average = passing = 0
        total_scored = 0

    return render(
        request,
        'scores/score_view.html',
        {
            'section': section,
            'subject': subject,
            'activity': activity,
            'enrollments': enrollments,
            'score_map': score_map,
            'highest': highest,
            'lowest': lowest,
            'average': round(average, 2) if average else 0,
            'passing': passing,
            'total_scored': total_scored,
        }
    )

@login_required
def student_score_view(request, section_pk, subject_pk, enrollment_pk):
    section = get_object_or_404(Section, pk=section_pk)
    subject = get_object_or_404(Subject, pk=subject_pk)
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)

    # Get active term
    try:
        current_term = Term.objects.get(is_current=True)
    except Term.DoesNotExist:
        current_term = None

    # Get all graded activities for this subject and term
    activities = Activity.objects.filter(
        subject=subject,
        activity_type='graded',
        term=current_term
    ).order_by('component', 'date')

    # Get all scores for this student
    scores = Score.objects.filter(
        enrollment=enrollment,
        activity__subject=subject,
        activity__term=current_term
    ).select_related('activity')

    # Build score lookup
    score_map = {
        s.activity.pk: s for s in scores
    }

    # Group activities by component
    ww_activities = activities.filter(component='WW')
    pt_activities = activities.filter(component='PT')
    te_activities = activities.filter(component='TE')

    # Compute percentage per component
    def component_percentage(act_list):
        total_possible = sum(
            a.total_score for a in act_list
            if a.total_score
        )
        total_earned = sum(
            float(score_map[a.pk].score)
            for a in act_list
            if a.pk in score_map
            and score_map[a.pk].score is not None
        )
        if total_possible > 0:
            return round(
                (total_earned / total_possible) * 100, 2
            )
        return 0

    ww_percentage = component_percentage(ww_activities)
    pt_percentage = component_percentage(pt_activities)
    te_percentage = component_percentage(te_activities)

    # Get weights based on subject type
    from scores.constants import SUBJECT_WEIGHTS
    weights = SUBJECT_WEIGHTS.get(subject.subject_type, {
        'WW': 0.20, 'PT': 0.50, 'TE': 0.30
    })

    # Compute initial grade (before transmutation)
    initial_grade = (
        (ww_percentage * weights['WW']) +
        (pt_percentage * weights['PT']) +
        (te_percentage * weights['TE'])
    )

    # Transmute grade
    from scores.utils import transmute_grade
    quarterly_grade = transmute_grade(initial_grade)

    return render(request, 'scores/student_score_view.html', {
        'section': section,
        'subject': subject,
        'enrollment': enrollment,
        'current_term': current_term,
        'ww_activities': ww_activities,
        'pt_activities': pt_activities,
        'te_activities': te_activities,
        'score_map': score_map,
        'ww_percentage': ww_percentage,
        'pt_percentage': pt_percentage,
        'te_percentage': te_percentage,
        'weights': weights,
        'initial_grade': round(initial_grade, 2),
        'quarterly_grade': quarterly_grade,
    })