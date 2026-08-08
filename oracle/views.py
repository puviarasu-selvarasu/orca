from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .strategists import get_strategic_advice
from .predictors import predict_system_health

@login_required
def get_advice(request):
    advice = get_strategic_advice(request.user)
    return JsonResponse({'advice': advice})

@login_required
def get_prediction(request):
    pred = predict_system_health(request.user)
    return JsonResponse(pred if pred else {'error': 'Insufficient data'})