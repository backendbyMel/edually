from django.urls import path
from .views import record_attendance, update_or_create, attendance_history, student_attendance_history, student_attendance_detail, student_attendance_edit

urlpatterns = [
    path('record/', record_attendance, name='attendance-record'),
    path('record/create', update_or_create, name='attendance-create'),
    path('summary/',attendance_history, name='attendance-summary'),
    path('students/', student_attendance_history, name='attendance-student-summary'),
    path('student/<int:enrollment_pk>/',student_attendance_detail, name='attendance-student-detail'),
    path('student/<int:attendance_pk>/edit',student_attendance_edit, name='attendance-student-edit'),
]