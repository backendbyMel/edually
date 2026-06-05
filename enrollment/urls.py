from django.urls import path
from .views import search_student, enroll_student, enroll_delete

urlpatterns = [
    path('search/', search_student,name='search-student'),  
    path('enroll/<int:student_pk>', enroll_student,name='enroll-student'),  
    path('unenroll/<int:enrollment_pk>', enroll_delete,name='enroll-delete'), 
]