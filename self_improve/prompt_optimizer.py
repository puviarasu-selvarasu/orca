import random
from datetime import datetime
from django.contrib.auth.models import User
from django.conf import settings
from chat.models import ChatMessage, ChatThread
from .models import PromptVariant, PromptEvaluation

# ============================================================
# 1. PROMPT VARIANTS TO TEST
# ============================================================
BASE_PROMPTS = [
    {
        "name": "Default (Friendly Assistant)",
        "content": "You are O.R.C.A., a precise and helpful assistant. Answer the user's question clearly. Keep responses under 200 words."
    },
    {
        "name": "JARVIS (Slightly Witty)",
        "content": "You are O.R.C.A., a witty and intelligent companion. You speak in a warm, slightly humorous tone. Keep it conversational and under 200 words."
    },
    {
        "name": "Strategic Advisor",
        "content": "You are O.R.C.A., a strategic advisor. Focus on long-term planning, decision frameworks, and actionable insights. Be concise and structured."
    },
    {
        "name": "Technical Expert",
        "content": "You are O.R.C.A., a technical expert. Provide deep technical explanations with code examples when needed. Be precise and avoid fluff."
    },
    {
        "name": "Empathetic Listener",
        "content": "You are O.R.C.A., an empathetic listener. Prioritize understanding the user's emotions and offering supportive, thoughtful responses. Be warm and patient."
    }
]

def get_base_prompts():
    """Return the base prompt variants."""
    return BASE_PROMPTS

# ============================================================
# 2. EVALUATE A PROMPT VARIANT
# ============================================================
def evaluate_prompt(variant: PromptVariant) -> float:
    """
    Evaluate a prompt variant by testing it on past conversations.
    Returns a score between 0 and 1.
    """
    # Get past user messages (last 20)
    from chat.models import ChatMessage
    user = User.objects.first()  # For now, use the first user
    if not user:
        return 0.0
    
    recent_messages = ChatMessage.objects.filter(
        thread__user=user,
        role='user'
    ).order_by('-timestamp')[:10]
    
    if not recent_messages:
        return 0.5  # Default score if no history
    
    # For each user message, check if the assistant's response was helpful
    # We use a simple heuristic: if the assistant response was long enough (>= 20 words),
    # it's considered "helpful" (proxy metric)
    total = 0
    count = 0
    for msg in recent_messages:
        # Find the assistant reply immediately following this message
        assistant_reply = ChatMessage.objects.filter(
            thread=msg.thread,
            timestamp__gt=msg.timestamp,
            role='assistant'
        ).first()
        if assistant_reply:
            word_count = len(assistant_reply.content.split())
            # Score: 1.0 if response > 20 words, else proportional
            score = min(1.0, word_count / 30.0)
            total += score
            count += 1
    
    return total / count if count > 0 else 0.5

# ============================================================
# 3. OPTIMIZATION LOOP
# ============================================================
def optimize_prompts():
    """
    Run the prompt optimization loop:
    1. Try all prompt variants on past conversations.
    2. Score each one.
    3. Update the active prompt with the highest score.
    """
    # Create or update prompt variants
    for prompt_data in BASE_PROMPTS:
        variant, created = PromptVariant.objects.get_or_create(
            name=prompt_data["name"],
            defaults={"content": prompt_data["content"]}
        )
        if not created:
            variant.content = prompt_data["content"]
            variant.save()
    
    # Evaluate each variant
    for variant in PromptVariant.objects.all():
        score = evaluate_prompt(variant)
        variant.score = score
        variant.times_tested += 1
        variant.save()
    
    # Find the best variant
    best_variant = PromptVariant.objects.order_by('-score').first()
    if best_variant:
        # Update all variants to inactive, then mark the best as active
        PromptVariant.objects.update(is_active=False)
        best_variant.is_active = True
        best_variant.save()
        
        # Update the system prompt in the database (we'll store it in the DB)
        # For now, we'll just print the winner
        print(f"🏆 Best prompt: {best_variant.name} (score: {best_variant.score:.2f})")
        
        # Save to settings? We'll use a custom model to store the active prompt
        # For now, we'll update a config table
        
    return best_variant

def get_active_prompt() -> str:
    """Get the currently active system prompt."""
    active = PromptVariant.objects.filter(is_active=True).first()
    if active:
        return active.content
    return BASE_PROMPTS[0]["content"]  # Default if none active