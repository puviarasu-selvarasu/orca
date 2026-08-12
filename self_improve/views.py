from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .prompt_optimizer import optimize_prompts

@login_required
def run_optimization(request):
    """Manually trigger prompt optimization."""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        best = optimize_prompts()
        return JsonResponse({
            'status': 'success',
            'best_prompt': best.name if best else None,
            'score': best.score if best else None
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)