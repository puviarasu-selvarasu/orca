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


# ============================================================
# VIEW: DASHBOARD (With Chat History)
# ============================================================
@login_required
def dashboard(request):
    """Main O.R.C.A. dashboard with persistent chat history."""
    threads = ChatThread.objects.filter(user=request.user)
    
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
    """Streaming chat endpoint with RAG + Local LLM + Persistence + Smart Filler Detection."""
    thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
    except:
        user_message = ''
    
    if not user_message:
        return JsonResponse({'error': 'Message is empty'}, status=400)

    # Truncate user message to avoid token overflow
    MAX_USER_MSG_CHARS = 400
    if len(user_message) > MAX_USER_MSG_CHARS:
        user_message = user_message[:MAX_USER_MSG_CHARS] + "\n\n... (truncated to {} characters)".format(MAX_USER_MSG_CHARS)
    
    # 1. SAVE USER MESSAGE
    ChatMessage.objects.create(
        thread=thread,
        role='user',
        content=user_message
    )
    
    # 2. UPDATE THREAD TITLE
    if thread.messages.count() == 1:
        title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        thread.title = title
        thread.save()
    
    # ============================================================
    # 3. SMART FILLER DETECTION (Prevents ML lectures for "okay")
    # ============================================================
    filler_phrases = ['okay', 'got it', 'thanks', 'thank you', 'cool', 'nice', 'alright', 'sure', 'fine']
    
    # Check if the message is a short filler
    is_filler = (
        len(user_message.split()) <= 3 and 
        any(phrase in user_message.lower() for phrase in filler_phrases)
    )
    
    context = ""
    if is_filler:
        # Skip RAG entirely for filler messages
        context = "The user is just acknowledging or confirming. Keep your response warm, brief, and conversational. Do not inject technical content or code."
    else:
        # 4. RETRIEVE RELEVANT CHUNKS FROM CHROMADB (RAG)
        relevant_chunks, metadatas = query_knowledge(user_message, n_results=3)
        context = "\n\n".join(relevant_chunks) if relevant_chunks else "No relevant documents found."
    
    # 5. BUILD THE PROMPT
    system_prompt = f"""You are O.R.C.A., a precise and helpful assistant. Answer the user's question clearly.

RULES:
- If the user says "okay", "got it", or similar, give a short, friendly acknowledgment.
- Do not generate code or technical deep-dives unless explicitly asked.
- Keep responses under 200 words.

Context from the user's knowledge base (use only if relevant to their specific question):
{context}

The user asks: {user_message}

Your response:"""
    
    # 6. STREAM RESPONSE
    full_response = ""
    
    def generate():
        nonlocal full_response
        for token in generate_stream(system_prompt, max_tokens=512):
            full_response += token
            yield f"data: {token}\n\n"
        
        ChatMessage.objects.create(
            thread=thread,
            role='assistant',
            content=full_response
        )
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
    threads = ChatThread.objects.filter(user=request.user)
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