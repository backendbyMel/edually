from django.urls import path
from . import views

urlpatterns = [
    path('subject/<int:subject_pk>/activities/',views.ActivityListView.as_view(), name='activity-list'),
    path('subject/<int:subject_pk>/activities/create/',views.ActivityCreateView.as_view(),name='activity-create'),
    path('subject/<int:subject_pk>/activities/<int:pk>/update/',views.ActivityUpdateView.as_view(),name='activity-update'),
    path('subject/<int:subject_pk>/activities/<int:pk>/delete/', views.ActivityDeleteView.as_view(), name='activity-delete'),
    path('subject/<int:subject_pk>/activities/<int:activity_pk>/scores/',views.score_input,name='score-input'),
    path('subject/<int:subject_pk>/activities/<int:activity_pk>/scores/view/',views.score_view,name='score-view'),
]