from .constants import SUBJECT_WEIGHTS
from .models import Activity, Score

def compute_quarterly_grade(enrollment, subject, term):
    weights = SUBJECT_WEIGHTS.get(subject.subject_type)

    if not weights:
        return None

    # Get all graded activities per component
    def get_component_percentage(component):
        activities = Activity.objects.filter(
            subject=subject,
            term=term,
            component=component,
            activity_type='graded'
        )

        total_possible = sum(
            a.total_score for a in activities
            if a.total_score
        )

        if total_possible == 0:
            return 0

        total_earned = 0
        for activity in activities:
            score_obj = Score.objects.filter(
                activity=activity,
                enrollment=enrollment
            ).first()
            if score_obj and score_obj.score:
                total_earned += float(score_obj.score)

        return (total_earned / total_possible) * 100

    ww_percentage = get_component_percentage('WW')
    pt_percentage = get_component_percentage('PT')
    te_percentage = get_component_percentage('TE')

    quarterly_grade = (
        (ww_percentage * weights['WW']) +
        (pt_percentage * weights['PT']) +
        (te_percentage * weights['TE'])
    )

    # DepEd transmutation
    # Ask yourself: "Does DepEd use raw percentage or transmuted grade?"
    transmuted = transmute_grade(quarterly_grade)

    return round(transmuted, 2)


def transmute_grade(percentage):
    # DepEd transmutation table
    # Hint: research DepEd Order No. 8 s. 2015
    transmutation_table = [
        (100, 100), (98.40, 99), (96.80, 98),
        (95.20, 97), (93.60, 96), (92.00, 95),
        (90.40, 94), (88.80, 93), (87.20, 92),
        (85.60, 91), (84.00, 90), (82.40, 89),
        (80.80, 88), (79.20, 87), (77.60, 86),
        (76.00, 85), (74.40, 84), (72.80, 83),
        (71.20, 82), (69.60, 81), (68.00, 80),
        (66.40, 79), (64.80, 78), (63.20, 77),
        (61.60, 76), (60.00, 75), (56.00, 74),
        (52.00, 73), (48.00, 72), (44.00, 71),
        (40.00, 70), (36.00, 69), (32.00, 68),
        (28.00, 67), (24.00, 66), (20.00, 65),
        (16.00, 64), (12.00, 63), (8.00, 62),
        (4.00, 61), (0.00, 60),
    ]

    for raw, transmuted in transmutation_table:
        if percentage >= raw:
            return transmuted

    return 60