from django.db.models import Count
from django.db.models.functions import TruncDate
from chat.models import ChatMessage

def get_system_metrics_aggregated(user):
    """
    Pull daily message counts for the given user using ORM (safe and correct).
    Returns a list of dicts: [{'date': '2026-08-08', 'count': 5}, ...]
    """
    qs = (
        ChatMessage.objects
        .filter(thread__user=user)  # Fixed: use thread__user
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')[:30]
    )
    
    return [{'date': item['date'].isoformat(), 'count': item['count']} for item in qs]