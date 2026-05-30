from django.urls import path
from .views import (schoolYearCreate)

urlpatterns = [
    path('create/', schoolYearCreate.as_view(), name='schoolYear-create'),
]