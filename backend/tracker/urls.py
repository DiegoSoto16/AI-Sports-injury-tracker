from django.urls import path
from . import views

urlpatterns = [
    path('athletes/', views.get_all_athletes, name='get_all_athletes'),
    path('predictions/', views.get_all_predictions, name='get_all_predictions'),
    path('predict/', views.predict_view, name='predict_view'),
]
