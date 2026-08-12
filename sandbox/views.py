import os
import tempfile
import cv2

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .vision_engine import analyze_image

@login_required
@csrf_exempt
def upload_image(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image uploaded'}, status=400)
    
    uploaded_file = request.FILES['image']
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    
    try:
        description = analyze_image(tmp_path)
        return JsonResponse({'description': description})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        os.unlink(tmp_path)

@login_required
@csrf_exempt
def physical_vision(request):
    """Capture webcam frame and analyze it with Moondream."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    if cv2 is None:
        return JsonResponse({'error': 'OpenCV is not installed'}, status=500)
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return JsonResponse({'error': 'Webcam not accessible'}, status=500)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return JsonResponse({'error': 'Failed to capture frame'}, status=500)
        
        # Save frame temporarily
        temp_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
        cv2.imwrite(temp_path, frame)
        
        # Analyze
        description = analyze_image(temp_path, "Describe what you see in detail.")
        
        # Clean up
        os.unlink(temp_path)
        
        return JsonResponse({'description': description})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
