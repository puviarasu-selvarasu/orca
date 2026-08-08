import json
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .filesystem import safe_write_file, safe_execute_command
from .plan_generator import generate_plan

# ============================================================
# ORACLE INTEGRATION (Phase 9)
# ============================================================
try:
    from oracle.predictors import predict_build_success
except ImportError:
    # Fallback if oracle app is not installed yet
    def predict_build_success(user, project_type, file_count):
        return {'success_probability': 0.9, 'confidence': 0.5}

# ============================================================
# BACKGROUND TASK EXECUTOR
# ============================================================
executor = ThreadPoolExecutor(max_workers=2)
tasks = {}  # Simple in-memory task storage {task_id: {status, result}}

def run_ai_plan_task(task_id, description):
    """Background task: generates AI plan and stores it."""
    try:
        plan = generate_plan(description)
        tasks[task_id] = {'status': 'completed', 'result': plan}
    except Exception as e:
        tasks[task_id] = {'status': 'failed', 'error': str(e)}


# ============================================================
# VIEW: INSTANT MOCK PLAN (Fast)
# ============================================================
@login_required
@csrf_exempt
def builder_preview(request):
    """Returns an instant mock plan (<1 second)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        description = data.get('description', '')
    except:
        description = ''
    
    if not description:
        return JsonResponse({'error': 'Empty description'}, status=400)
    
    # Instant mock plan (Django boilerplate)
    mock_plan = {
        'project_name': 'my_app',
        'files': [
            {'path': 'my_app/requirements.txt', 'content': 'django==4.2.7\nrequests\npillow\n'},
            {'path': 'my_app/app.py', 'content': 'print("Hello, O.R.C.A.!")\n'}
        ],
        'commands': [
            'pip install -r my_app/requirements.txt',
            'python my_app/app.py'
        ]
    }
    
    return JsonResponse({
        'status': 'success',
        'plan': mock_plan,
        'is_mock': True  # Flag so UI knows it's a mock
    })


# ============================================================
# VIEW: START BACKGROUND AI PLAN (Non-blocking)
# ============================================================
@login_required
@csrf_exempt
def builder_ai_preview(request):
    """Starts a background task to generate an AI plan."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        description = data.get('description', '')
    except:
        description = ''
    
    if not description:
        return JsonResponse({'error': 'Empty description'}, status=400)
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing', 'result': None}
    
    # Run in background thread
    executor.submit(run_ai_plan_task, task_id, description)
    
    return JsonResponse({
        'status': 'started',
        'task_id': task_id
    })


# ============================================================
# VIEW: CHECK AI PLAN STATUS
# ============================================================
@login_required
def builder_ai_status(request, task_id):
    """Poll this endpoint to check if the AI plan is ready."""
    task = tasks.get(task_id)
    if not task:
        return JsonResponse({'error': 'Invalid task ID'}, status=404)
    
    return JsonResponse(task)


# ============================================================
# VIEW: EXECUTE PLAN (With Oracle Integration)
# ============================================================
@login_required
@csrf_exempt
def builder_execute(request):
    """Execute an approved build plan with Oracle strategic warnings."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        plan = data.get('plan', {})
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if not plan:
        return JsonResponse({'error': 'Empty plan'}, status=400)
    
    results = []
    
    # ============================================================
    # ORACLE: Predict build success before execution
    # ============================================================
    try:
        # Detect project type from files
        project_type = 'python'  # default
        files = plan.get('files', [])
        for file_info in files:
            path = file_info.get('path', '')
            if path.endswith('.php') or 'composer.json' in path:
                project_type = 'php'
                break
            elif path.endswith('.java') or 'pom.xml' in path:
                project_type = 'java'
                break
        
        file_count = len(files)
        pred = predict_build_success(request.user, project_type, file_count)
        
        if pred and pred.get('success_probability', 1.0) < 0.6:
            warning_msg = (
                f"⚠️ Strategic Warning: Build success probability is low ({pred['success_probability']:.0%}). "
                f"Confidence: {pred.get('confidence', 0.5):.0%}. "
                "Please review your dependencies and configuration before proceeding."
            )
            results.append(warning_msg)
        elif pred:
            results.append(f"✅ Strategic Check: Build success probability is {pred['success_probability']:.0%}.")
    except Exception as e:
        results.append(f"⚠️ Oracle error: {str(e)}")
    
    # ============================================================
    # 1. Write files
    # ============================================================
    files = plan.get('files', [])
    for file_info in files:
        path = file_info.get('path', '')
        content = file_info.get('content', '')
        
        if not path or not content:
            continue
        
        # Scan code if it's a Python file
        if path.endswith('.py'):
            from .ast_scanner import scan_code
            is_safe, msg = scan_code(content)
            if not is_safe:
                results.append(f"⛔ {msg} (in {path})")
                continue
        elif path.endswith(('.php', '.java', '.xml', '.properties', '.yml', '.yaml', '.json')):
            results.append(f"⚠️ Security scan skipped for {path}. Please review manually.")
        # For other file types, just write without scanning
        
        result = safe_write_file(path, content)
        results.append(result)
    
    # ============================================================
    # 2. Execute commands
    # ============================================================
    commands = plan.get('commands', [])
    for cmd in commands:
        result = safe_execute_command(cmd, timeout=30)
        results.append(f"$ {cmd}\n{result}")
    
    return JsonResponse({
        'status': 'completed',
        'results': results
    })


# ============================================================
# VIEW: SELF-HEAL ENDPOINT (Optional)
# ============================================================
@login_required
@csrf_exempt
def self_heal_endpoint(request):
    """Self-heal endpoint – fixes broken code based on error logs."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        project_path = data.get('project_path', '')
        error_log = data.get('error_log', '')
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if not project_path or not error_log:
        return JsonResponse({'error': 'Missing project_path or error_log'}, status=400)
    
    try:
        from .self_heal import self_heal
        result = self_heal(project_path, error_log)
        return JsonResponse(result)
    except ImportError:
        return JsonResponse({'error': 'Self-heal module not implemented yet.'}, status=501)

@login_required
@csrf_exempt
def upload_requirements(request):
    """Upload a file, extract text via OCR, and return the content."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    uploaded_file = request.FILES['file']
    
    # Security: Limit file size to 5MB
    if uploaded_file.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'File too large. Max 5MB.'}, status=400)
    
    # Security: Restrict file types
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.pdf', '.txt', '.md', '.py', '.js', '.html', '.css', '.json']
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in allowed_extensions:
        return JsonResponse({'error': f'Unsupported file type: {ext}'}, status=400)
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        # Extract text
        from .ocr_extractor import extract_text_from_file
        extracted_text = extract_text_from_file(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        if extracted_text.startswith("❌"):
            return JsonResponse({'error': extracted_text}, status=400)
        
        # ============================================================
        # STEP 4: TRUNCATE AND ADD FLAGS
        # ============================================================
        original_len = len(extracted_text)
        MAX_CHARS = 400
        truncated = False
        
        if original_len > MAX_CHARS:
            truncated = True
            extracted_text = extracted_text[:MAX_CHARS] + "\n\n... (truncated to {} characters to fit the AI's context window)".format(MAX_CHARS)
        
        return JsonResponse({
            'status': 'success',
            'filename': uploaded_file.name,
            'text': extracted_text,
            'truncated': truncated,
            'original_length': original_len
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to process file: {str(e)}'}, status=500)