from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_view, name='predict'),
    path('predictions/', views.get_all_predictions, name='get_all_predictions'),
    path('athletes/', views.get_all_athletes, name='get_all_athletes'),
]
