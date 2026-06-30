from django.urls import path
from .views import (StudentListView, 
                    StudentCreateView, 
                    StudentDetailView, 
                    StudentUpdateView, 
                    StudentDeleteView,
                    download_student_template)

urlpatterns = [
    path('', StudentListView.as_view(),name='student-home'),
    path('detail/<int:pk>', StudentDetailView.as_view(),name='student-detail'),
    path('detail/<int:pk>/update', StudentUpdateView.as_view(),name='student-update'),
    path('create/', StudentCreateView.as_view(),name='student-create'),
    path('detail/<int:pk>/delete', StudentDeleteView.as_view(),name='student-delete'),
    path('import/template/<str:fmt>/',download_student_template,name='download-student-template',),
]