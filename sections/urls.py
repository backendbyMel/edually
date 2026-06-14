from django.urls import path, include
from .views import (SectionListView, 
                    SectionDetailView, 
                    SectionCreateView, 
                    SectionUpdateView, 
                    SectionDeleteView,
                    SubjectCreateView,
                    SubjectUpdateView,
                    SubjectDeleteView,
                    SectionMasterlistDocxView)
urlpatterns = [
    path('detail/<int:section_pk>/', include('enrollment.urls')),
    path('detail/<int:section_pk>/attendance/',include('attendance.urls')),
    path('detail/<int:section_pk>/',include('scores.urls')),
    path('', SectionListView.as_view(),name='section-home'),
    path('detail/<int:pk>', SectionDetailView.as_view(),name='section-detail'),
    path('detail/<int:pk>/update', SectionUpdateView.as_view(),name='section-update'),
    path('create/', SectionCreateView.as_view(),name='section-create'),
    path('detail/<int:pk>/delete', SectionDeleteView.as_view(),name='section-delete'),
    path('detail/<int:pk>/subject/create/', SubjectCreateView.as_view(),name='subject-create'),
    path('detail/<int:section_pk>/subject/update/<int:subject_pk>', SubjectUpdateView.as_view(),name='subject-update'),
    path('detail/<int:section_pk>/subject/delete/<int:pk>', SubjectDeleteView.as_view(),name='subject-delete'),
    path('detail/<int:pk>/masterlist/', SectionMasterlistDocxView.as_view(),name='section-masterlist-docx'),
    
]