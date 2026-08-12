"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from django.views.generic import TemplateView
from chat import views as chat_views
from sandbox import builder as builder_views
from oracle import views as oracle_views
from voice import views as voice_views
from sandbox import views as sandbox_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Main dashboard (shows latest thread)
    path('', chat_views.dashboard, name='dashboard'),
    
    # Thread management APIs
    path('api/threads/', chat_views.list_threads, name='list_threads'),
    path('api/threads/create/', chat_views.create_thread, name='create_thread'),
    path('api/threads/<int:thread_id>/delete/', chat_views.delete_thread, name='delete_thread'),
    path('api/threads/<int:thread_id>/messages/', chat_views.get_messages, name='get_messages'),
    
    # Chat stream (passes thread_id)
    path('api/chat/<int:thread_id>/stream/', chat_views.chat_stream, name='chat_stream'),
    
    # System metrics
    path('metrics/', chat_views.system_metrics, name='system_metrics'),

    path('api/builder/preview/', builder_views.builder_preview, name='builder_preview'),
    path('api/builder/execute/', builder_views.builder_execute, name='builder_execute'),

    path('api/builder/preview/', builder_views.builder_preview, name='builder_preview'),
    path('api/builder/ai-plan/', builder_views.builder_ai_preview, name='builder_ai_preview'),
    path('api/builder/ai-plan/status/<str:task_id>/', builder_views.builder_ai_status, name='builder_ai_status'),
    path('api/builder/execute/', builder_views.builder_execute, name='builder_execute'),

    path('api/oracle/advice/', oracle_views.get_advice, name='oracle_advice'),
    path('api/oracle/prediction/', oracle_views.get_prediction, name='oracle_prediction'),

    path('api/builder/upload-requirements/', builder_views.upload_requirements, name='upload_requirements'),

    # ... existing ...
    path('api/stt/', voice_views.speech_to_text, name='speech_to_text'),
    path('api/tts/', voice_views.text_to_speech, name='text_to_speech'),
    path('api/vision/upload/', sandbox_views.upload_image, name='upload_image'),

    path('jarvis/', TemplateView.as_view(template_name='jarvis/jarvis.html'), name='jarvis'),
    path('api/vision/physical/', sandbox_views.physical_vision, name='physical_vision'),
    path('api/jarvis/thread/', chat_views.get_or_create_jarvis_thread, name='jarvis_thread'),

    path('api/memory/save/', chat_views.save_memory, name='save_memory'),

]