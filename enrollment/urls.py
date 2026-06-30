from django.urls import path
#from .views import search_student, enroll_student, enroll_delete, bulk_enroll_students, download_student_template
from .views import search_student, enroll_student, enroll_delete, bulk_enroll_students
urlpatterns = [
    path('search/', search_student,name='search-student'),  
    path('enroll/<int:student_pk>', enroll_student,name='enroll-student'),  
    path('unenroll/<int:enrollment_pk>', enroll_delete,name='enroll-delete'), 
    path('bulk-enroll/', bulk_enroll_students, name='bulk-enroll-students',),
 
    # ── NEW: Download import template ─────────────────────────────────────
    # fmt = 'xlsx' or 'csv'
    #path('import/template/<str:fmt>/',download_student_template,name='download-student-template',),
]