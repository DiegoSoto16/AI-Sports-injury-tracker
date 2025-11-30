from django.contrib import admin
from django.urls import path, include
from tracker import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tracker.urls')),
    path("athletes/<int:pk>/workload/", views.athlete_workload),
]
