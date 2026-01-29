"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import TemplateView
from learning_session.views_analytics import get_available_topics

def home(request):
    return JsonResponse({
        "message": "Welcome to the Personal Tutoring API",
        "endpoints": {
            "admin": "/admin/",
            "users": "/api/users/",
            "core": "/api/core/"
        }
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/core/', include('core.urls')),
    path('api/ai/', include('ai_engine.urls')),
    path('api/gaps/', include('learning_session.urls')),  # Gap implementations
    path('api/sessions/', include('learning_session.urls')),  # Analytics endpoints
    path('api/topics/available/', get_available_topics, name='topics_available'),
    
    # Frontend HTML pages
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login.html', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register.html', TemplateView.as_view(template_name='register.html'), name='register'),
    path('dashboard.html', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('voice.html', TemplateView.as_view(template_name='voice.html'), name='voice'),
    path('editor.html', TemplateView.as_view(template_name='editor.html'), name='editor'),
    path('canvas.html', TemplateView.as_view(template_name='canvas.html'), name='canvas'),
    path('assessment.html', TemplateView.as_view(template_name='assessment.html'), name='assessment'),
]
