from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WearableData
import json

@csrf_exempt
def upload_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entry = WearableData.objects.create(
                heart_rate=data['heart_rate'],
                fatigue_level=data['fatigue_level'],
                sleep_hours=data['sleep_hours'],
                steps=data['steps']
            )
            return JsonResponse({'status': 'success', 'id': entry.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def latest_data(request):
    latest = WearableData.objects.last()
    if latest:
        return JsonResponse({
            'heart_rate': latest.heart_rate,
            'fatigue_level': latest.fatigue_level,
            'sleep_hours': latest.sleep_hours,
            'steps': latest.steps,
            'timestamp': latest.timestamp
        })
    return JsonResponse({'error': 'No data found'}, status=404)
