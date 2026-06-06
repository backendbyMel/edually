from django.urls import path
from .views import (TermCreate)

urlpatterns = [
    path('create/', TermCreate.as_view(), name='schoolYear-create'),
]