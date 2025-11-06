from django.urls import path
from . import views

urlpatterns = [
    path('athletes/', views.get_all_athletes, name='get_all_athletes'),
    path('predict/', views.predict_injury, name='predict_injury'),
    path('predictions/', views.get_prediction_history,
         name='get_prediction_history'),
]
