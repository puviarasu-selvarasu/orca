import json
import psutil
from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rag.ingestion import query_knowledge
from chat.llm_wrapper import generate_stream
from chat.models import ChatThread, ChatMessage
from .router import route_query


# ============================================================
# VIEW: DASHBOARD (With Chat History)
# ============================================================
@login_required
def dashboard(request):
    """Main O.R.C.A. dashboard with persistent chat history."""
    threads = ChatThread.objects.filter(user=request.user).exclude(title="JARVIS Voice")
    
    current_thread = threads.first()
    if not current_thread:
        current_thread = ChatThread.objects.create(user=request.user, title="New Conversation")
        threads = ChatThread.objects.filter(user=request.user)
    
    messages = ChatMessage.objects.filter(thread=current_thread).order_by('timestamp')
    chat_history = [{'role': msg.role, 'content': msg.content} for msg in messages]
    
    threads_data = [{'id': t.id, 'title': t.title, 'updated_at': t.updated_at.isoformat()} for t in threads]
    
    return render(request, 'chat/dashboard.html', {
        'user': request.user,
        'threads': threads_data,
        'current_thread_id': current_thread.id,
        'chat_history': chat_history,
    })


# ============================================================
# VIEW: SYSTEM METRICS (CPU / RAM)
# ============================================================
def system_metrics(request):
    """Real-time system metrics endpoint."""
    return JsonResponse({
        'cpu': psutil.cpu_percent(interval=0.5),
        'ram': psutil.virtual_memory().percent,
    })


# ============================================================
# VIEW: CHAT STREAM (RAG + LLM + Persistence + Friendly Persona)
# ============================================================
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_stream(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
    except:
        user_message = ''

    if not user_message:
        return JsonResponse({'error': 'Message is empty'}, status=400)

    # ============================================================
    # DETECT LANGUAGE
    # ============================================================
    detected_lang = detect_language(user_message)
    language_instruction = ""
    if detected_lang == 'ta':
        language_instruction = "IMPORTANT: The user wrote in Tamil. You MUST respond in Tamil. Do not respond in English."

    # 1. SAVE USER MESSAGE
    ChatMessage.objects.create(thread=thread, role='user', content=user_message)

    # 2. UPDATE THREAD TITLE
    if thread.messages.count() == 1:
        title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        thread.title = title
        thread.save()

    # 3. RAG RETRIEVAL
    relevant_chunks, metadatas = query_knowledge(user_message, n_results=3)
    context = "\n\n".join(relevant_chunks) if relevant_chunks else "No relevant documents found."

    # 4. BUILD THE PROMPT
    system_prompt = f"""You are O.R.C.A., a precise and helpful assistant.

{language_instruction}

Context from user's knowledge base:
{context}

User question: {user_message}

Your response:"""

    # 5. STREAM RESPONSE
    full_response = ""

    def generate():
        nonlocal full_response
        for token in generate_stream(system_prompt, max_tokens=512):
            full_response += token
            yield f"data: {token}\n\n"

        ChatMessage.objects.create(thread=thread, role='assistant', content=full_response)
        thread.save()
        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(generate(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache, no-transform'
    response['X-Accel-Buffering'] = 'no'
    return response

# ============================================================
# API: LIST THREADS
# ============================================================
@login_required
def list_threads(request):
    threads = ChatThread.objects.filter(user=request.user).exclude(title="JARVIS Voice")
    data = [{'id': t.id, 'title': t.title, 'updated_at': t.updated_at.isoformat()} for t in threads]
    return JsonResponse({'threads': data})


# ============================================================
# API: CREATE THREAD
# ============================================================
@login_required
@require_http_methods(["POST"])
def create_thread(request):
    thread = ChatThread.objects.create(user=request.user, title="New Conversation")
    return JsonResponse({'id': thread.id, 'title': thread.title})


# ============================================================
# API: DELETE THREAD
# ============================================================
@login_required
@require_http_methods(["DELETE"])
def delete_thread(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
    thread.delete()
    return JsonResponse({'status': 'deleted'})


# ============================================================
# API: GET MESSAGES FOR A THREAD
# ============================================================
@login_required
def get_messages(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
    messages = ChatMessage.objects.filter(thread=thread).order_by('timestamp')
    data = [{'role': m.role, 'content': m.content} for m in messages]
    return JsonResponse({'messages': data})

@login_required
def get_or_create_jarvis_thread(request):
    thread, created = ChatThread.objects.get_or_create(
        user=request.user,
        title="JARVIS Voice",
        defaults={"title": "JARVIS Voice"}
    )
    return JsonResponse({'id': thread.id, 'title': thread.title, 'created': created})

import re

def detect_language(text):
    """
    Detect if the text is Tamil (contains Tamil Unicode characters).
    Returns 'ta' for Tamil, 'en' for English.
    """
    # Tamil Unicode range: 0x0B80 to 0x0BFF
    tamil_pattern = re.compile(r'[\u0B80-\u0BFF]')
    if tamil_pattern.search(text):
        return 'ta'
    return 'en'