from .models import StrategicAdvice
from chat.models import ChatMessage

def get_strategic_advice(user):
    """Generate strategic advice based on analytics."""
    advice = []
    
    # 1. Knowledge Gap Strategist
    user_msgs = ChatMessage.objects.filter(thread__user=user, role='user')
    
    topics = {}
    for msg in user_msgs:
        content = msg.content.lower()
        if 'python' in content:
            topics['python'] = topics.get('python', 0) + 1
        elif 'sql' in content:
            topics['sql'] = topics.get('sql', 0) + 1
        elif 'django' in content:
            topics['django'] = topics.get('django', 0) + 1
        elif 'laravel' in content:
            topics['laravel'] = topics.get('laravel', 0) + 1
        elif 'spring' in content or 'java' in content:
            topics['java'] = topics.get('java', 0) + 1
        elif 'game' in content or 'pygame' in content:
            topics['game'] = topics.get('game', 0) + 1
    
    if topics:
        weak = min(topics, key=topics.get)
        advice.append({
            'category': 'knowledge',
            'message': f"You ask few questions about {weak}. Consider studying it using your uploaded PDFs.",
            'action_url': '/knowledge'
        })
    
    # 2. System Health Strategist
    msg_count = user_msgs.count()
    if msg_count > 10:
        advice.append({
            'category': 'system',
            'message': f"You have {msg_count} messages in your chat history. Consider organizing your threads for better context.",
            'action_url': None
        })
    
    return advice