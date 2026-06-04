from django.urls import path
from .views import search_student, enroll_student

urlpatterns = [
    path('', search_student,name='search-student'),  
    path('enroll/<int:student_pk>', enroll_student,name='enroll-student'),  
]