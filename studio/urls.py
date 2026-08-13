from django.urls import path
from . import views

urlpatterns = [
    # Studio main page
    path('', views.studio_dashboard, name='studio_dashboard'),
    
    # Project detail page
    path('<int:project_id>/', views.studio_dashboard, name='studio_detail'),
    
    # API: Create project from plan
    path('api/projects/create/', views.create_project_from_plan, name='create_project_from_plan'),
    
    # API: Get project details
    path('api/project/<int:project_id>/', views.project_detail, name='project_detail'),
    
    # API: Project chat stream
    path('api/project/<int:project_id>/chat/stream/', views.project_chat_stream, name='project_chat_stream'),
    
    # API: Get file content
    path('api/project/<int:project_id>/file/', views.file_content, name='file_content'),
    
    # API: Delete message
    path('api/project/<int:project_id>/message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
]