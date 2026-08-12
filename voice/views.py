import os
import subprocess
import tempfile
import io
import winrt.windows.media.speechsynthesis as speech
import winrt.windows.storage.streams as streams
from django.http import FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from faster_whisper import WhisperModel

# ============================================================
# STT (Speech-to-Text) using faster-whisper
# ============================================================
stt_model = None

def get_stt_model():
    global stt_model
    if stt_model is None:
        stt_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return stt_model

@login_required
@csrf_exempt
def speech_to_text(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    if 'audio' not in request.FILES:
        return JsonResponse({'error': 'No audio file'}, status=400)
    
    audio_file = request.FILES['audio']
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    
    try:
        model = get_stt_model()
        segments, info = model.transcribe(tmp_path, beam_size=5)
        text = " ".join([seg.text for seg in segments])
        return JsonResponse({'text': text.strip()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        os.unlink(tmp_path)

# ============================================================
# TTS (Text-to-Speech) using Piper + Windows TTS for Tamil
# ============================================================
ENGLISH_MODEL = "models/en_US-lessac-medium.onnx"

def get_tamil_voice():
    try:
        voices = speech.SpeechSynthesizer.all_voices
        for voice in voices:
            if voice.language and "ta" in voice.language.lower():
                return voice
        return None
    except Exception as e:
        print(f"⚠️ Error getting Tamil voice: {e}")
        return None

def tts_tamil(text):
    voice = get_tamil_voice()
    if not voice:
        return None
    
    try:
        synthesizer = speech.SpeechSynthesizer()
        synthesizer.voice = voice
        stream = synthesizer.synthesize_text_to_stream_async(text).get()
        
        reader = streams.DataReader(stream)
        reader.load_async(stream.size).get()
        audio_bytes = bytearray(stream.size)
        reader.read_bytes(audio_bytes)
        
        return bytes(audio_bytes)
    except Exception as e:
        print(f"⚠️ Tamil TTS error: {e}")
        return None

@login_required
def text_to_speech(request):
    text = request.GET.get('text', '')
    language = request.GET.get('language', 'en')
    
    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)
    
    if len(text) > 500:
        text = text[:500] + "..."
    
    # 1. TRY WINDOWS TTS FOR TAMIL
    if language == 'ta':
        audio_data = tts_tamil(text)
        if audio_data:
            response = FileResponse(io.BytesIO(audio_data), content_type='audio/wav')
            response['Content-Disposition'] = 'inline; filename="speech.wav"'
            return response
    
    # 2. FALLBACK TO ENGLISH PIPER
    model_path = ENGLISH_MODEL
    if not os.path.exists(model_path):
        return JsonResponse({'error': f'Model not found: {model_path}'}, status=500)
    
    output_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    cmd = f'piper --model {model_path} --output_file {output_file} --text "{text}"'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        
        response = FileResponse(open(output_file, 'rb'), content_type='audio/wav')
        response['Content-Disposition'] = 'inline; filename="speech.wav"'
        return response
        
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        import atexit
        atexit.register(lambda: os.unlink(output_file) if os.path.exists(output_file) else None)