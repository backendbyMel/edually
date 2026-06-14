import datetime
from attendance.models import Attendance
from sections.models import Section
from enrollment.models import Enrollment

def attendance_alerts(request):
    if not request.user.is_authenticated:
        return {}

    today = datetime.date.today()
    unrecorded_count = 0

    adviser_sections = Section.objects.filter(
        adviser=request.user,
        is_adviser=True
    )

    for section in adviser_sections:
        has_students = Enrollment.objects.filter(
            section=section
        ).exists()

        if has_students:
            recorded = Attendance.objects.filter(
                enrollment__section=section,
                date=today
            ).exists()

            if not recorded:
                unrecorded_count += 1

    return {
        'unrecorded_count': unrecorded_count
    }