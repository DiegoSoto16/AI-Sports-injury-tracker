from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# simple welcome view (no separate file needed)


def home(request):
    return JsonResponse({
        "message": "Welcome to the AI Sports Injury Prevention API!",
        "endpoints": {
            "predict": "/api/predict/",
            "predictions": "/api/predictions/"
        },
        "info": "Use these API routes to test or integrate your backend with the frontend."
    })


urlpatterns = [
    path('', home),  # 👈 new homepage route
    path('admin/', admin.site.urls),
    # connects your tracker app routes
    path('api/', include('backend.tracker.urls')),
]
