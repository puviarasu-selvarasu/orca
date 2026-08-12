from django.urls import path
from . import views

urlpatterns = [
    path('api/self-improve/run/', views.run_optimization, name='run_optimization'),
]