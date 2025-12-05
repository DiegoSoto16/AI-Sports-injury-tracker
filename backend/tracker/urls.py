# backend/urls.py

from django.urls import path
from backend.tracker import views

urlpatterns = [
    # ---- Athletes ----
    path("athletes/", views.AthleteListView.as_view(), name="athlete-list"),
    path("athletes/<int:pk>/", views.AthleteDetailView.as_view(),
         name="athlete-detail"),

    # ---- Predictions ----
    path("predictions/", views.InjuryPredictionListView.as_view(),
         name="prediction-list"),
    path("predictions/latest/<int:athlete_id>/",
         views.latest_prediction, name="latest-prediction"),
    path("predict/", views.create_prediction, name="predict"),

    # ---- Sessions & history ----
    path("athletes/<int:athlete_id>/sessions/",
         views.athlete_sessions, name="athlete-sessions"),
    path("athletes/<int:athlete_id>/latest_session/",
         views.latest_session, name="athlete-latest-session"),
    path("athletes/<int:athlete_id>/history/",
         views.athlete_history, name="athlete-history"),
]
