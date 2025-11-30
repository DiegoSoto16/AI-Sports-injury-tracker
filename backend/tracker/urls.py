from django.urls import path
from . import views
from .views import latest_session
from .views import athlete_history

urlpatterns = [
    path('athletes/', views.AthleteListView.as_view(), name='athlete-list'),
    path('athletes/<int:pk>/', views.AthleteDetailView.as_view(),
         name='athlete-detail'),
    path('predictions/', views.InjuryPredictionListView.as_view(),
         name='prediction-list'),
    path("predictions/latest/<int:athlete_id>/",
         views.latest_prediction, name="latest-prediction"),
    path('predict/', views.create_prediction, name='create-prediction'),
    path("athletes/<int:athlete_id>/sessions/",
         views.athlete_sessions, name="athlete-sessions"),
    path("athletes/<int:athlete_id>/latest_session/",
         views.latest_session, name="athlete-latest-session"),
    path('athletes/<int:athlete_id>/latest_session/', latest_session),
    path("athletes/<int:pk>/history/", athlete_history),


]
