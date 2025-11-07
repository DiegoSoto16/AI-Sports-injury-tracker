from django.urls import path
from . import views

urlpatterns = [
    path('athletes/', views.AthleteListView.as_view(), name='athlete-list'),
    path('athletes/<int:pk>/', views.AthleteDetailView.as_view(),
         name='athlete-detail'),
    path('predictions/', views.InjuryPredictionListView.as_view(),
         name='prediction-list'),
    path("predictions/latest/<int:athlete_id>/",
         views.latest_prediction, name="latest-prediction"),
    path('predict/', views.create_prediction, name='create-prediction'),
]
