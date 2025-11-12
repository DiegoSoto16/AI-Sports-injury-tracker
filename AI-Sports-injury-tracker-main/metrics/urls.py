from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_data),
    path('latest/', views.latest_data),
]