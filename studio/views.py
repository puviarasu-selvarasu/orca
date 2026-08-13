import json
import os
import tempfile
import subprocess
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from backend import settings
from .models import Project, ProjectMessage
from chat.llm_wrapper import generate_stream
from rag.ingestion import query_knowledge

# ============================================================
# STUDIO DASHBOARD (with optional project_id)
# ============================================================
@login_required
def studio_dashboard(request, project_id=None):
    """Main Project Studio view."""
    projects = Project.objects.filter(user=request.user, is_active=True).order_by('-updated_at')
    
    current_project = None
    if project_id:
        current_project = get_object_or_404(Project, id=project_id, user=request.user)
    
    return render(request, 'studio/studio.html', {
        'projects': projects,
        'current_project': current_project,
        'project_id': current_project.id if current_project else None,
    })

# ============================================================
# API: PROJECT DETAIL
# ============================================================
@login_required
def project_detail(request, project_id):
    """Get project details including file tree and messages."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    messages = ProjectMessage.objects.filter(project=project).order_by('timestamp')
    return JsonResponse({
        'id': project.id,
        'name': project.name,
        'files': project.files,
        'commands': project.commands,
        'messages': [{'role': m.role, 'content': m.content, 'id': m.id} for m in messages],
    })

# ============================================================
# API: PROJECT CHAT STREAM
# ============================================================
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def project_chat_stream(request, project_id):
    """Streaming chat endpoint for project context."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
    except:
        user_message = ''
    
    if not user_message:
        return JsonResponse({'error': 'Message is empty'}, status=400)
    
    ProjectMessage.objects.create(project=project, role='user', content=user_message)
    
    file_tree = "\n".join([f"- {path}" for path in project.files.keys()])
    context = f"Project: {project.name}\n\nFiles:\n{file_tree}\n\nCommands: {', '.join(project.commands)}"
    
    system_prompt = f"""You are O.R.C.A., a precise and helpful assistant. The user is working on a project.

Current project context:
{context}

The user asks: {user_message}

Your response:"""
    
    full_response = ""
    
    def generate():
        nonlocal full_response
        for token in generate_stream(system_prompt, max_tokens=512):
            full_response += token
            yield f"data: {token}\n\n"
        
        ProjectMessage.objects.create(project=project, role='assistant', content=full_response)
        yield "data: [DONE]\n\n"
    
    response = StreamingHttpResponse(generate(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache, no-transform'
    response['X-Accel-Buffering'] = 'no'
    return response

# ============================================================
# API: FILE CONTENT
# ============================================================
@login_required
def file_content(request, project_id):
    """Get content of a specific file."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    path = request.GET.get('path', '')
    if path in project.files:
        return JsonResponse({'path': path, 'content': project.files[path]})
    return JsonResponse({'error': 'File not found'}, status=404)

# ============================================================
# API: DELETE MESSAGE
# ============================================================
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def delete_message(request, project_id, message_id):
    """Delete a message and all subsequent messages."""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    msg = get_object_or_404(ProjectMessage, id=message_id, project=project)
    ProjectMessage.objects.filter(project=project, timestamp__gte=msg.timestamp).delete()
    return JsonResponse({'status': 'deleted'})

# ============================================================
# API: CREATE PROJECT FROM PLAN (Fixed)
# ============================================================
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_project_from_plan(request):
    """Create a Project from a generated plan and write files to disk."""
    try:
        data = json.loads(request.body)
        # Check if plan is wrapped under a 'plan' key or sent directly
        plan = data.get('plan', data)
    except Exception as e:
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
    
    project_name = plan.get('project_name', 'Unnamed_Project')
    
    # Robustly parse files whether they come as a list, dict, or stringified JSON
    raw_files = plan.get('files', [])
    files_dict = {}
    
    if isinstance(raw_files, list):
        for f in raw_files:
            if isinstance(f, dict):
                path = f.get('path')
                content = f.get('content', '')
                if path:
                    files_dict[path] = content
    elif isinstance(raw_files, dict):
        files_dict = raw_files

    commands = plan.get('commands', [])
    
    if not files_dict:
        return JsonResponse({'error': 'No files in plan. Received files data was empty or invalid.'}, status=400)
    
    project = Project.objects.create(
        user=request.user, 
        name=project_name, 
        description="Generated project via O.R.C.A. engine",
        files=files_dict, 
        commands=commands, 
        is_active=True
    )
    
    # Write files to physical generated_projects/ folder
    base_dir = os.path.join(settings.BASE_DIR, 'generated_projects')
    project_dir = os.path.join(base_dir, str(project.id))
    os.makedirs(project_dir, exist_ok=True)
    
    for file_path, content in files_dict.items():
        full_path = os.path.join(project_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    return JsonResponse({
        'status': 'success', 
        'project_id': project.id, 
        'project_name': project.name
    })