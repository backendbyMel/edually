from django.urls import path
from .views import SectionListView, SectionDetailView, SectionCreateView, SectionUpdateView, SectionDeleteView

urlpatterns = [
    path('', SectionListView.as_view(),name='section-home'),
    path('detail/<int:pk>', SectionDetailView.as_view(),name='section-detail'),
    path('detail/<int:pk>/update', SectionUpdateView.as_view(),name='section-update'),
    path('create/', SectionCreateView.as_view(),name='section-create'),
    path('detail/<int:pk>/delete', SectionDeleteView.as_view(),name='section-delete'),
]