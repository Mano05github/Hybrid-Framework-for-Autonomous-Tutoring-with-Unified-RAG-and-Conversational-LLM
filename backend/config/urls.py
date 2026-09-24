"""
URL configuration for Vaathiyar project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import TemplateView


def home(request):
    return JsonResponse({
        "message": "Welcome to the Vaathiyar Tutoring API",
        "endpoints": {
            "admin":    "/admin/",
            "users":    "/api/users/",
            "core":     "/api/core/",
            "ai":       "/api/ai/",
            "sessions": "/api/sessions/",
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/users/',    include('users.urls')),
    path('api/core/',     include('core.urls')),
    path('api/ai/',       include('ai_engine.urls')),
    path('api/sessions/', include('learning_session.urls')),
    path('api/pbl/',      include('ai_engine.pbl.urls')),

    # Root API info
    path('api/', home, name='api_root'),

    # Frontend HTML pages (only files that actually exist in static_frontend/)
    path('', TemplateView.as_view(template_name='landing.html'), name='index'),
    path('login.html',            TemplateView.as_view(template_name='login.html'),            name='login'),
    path('register.html',         TemplateView.as_view(template_name='register.html'),         name='register'),
    path('dashboard.html',        TemplateView.as_view(template_name='dashboard.html'),        name='dashboard'),
    path('canvas.html',            TemplateView.as_view(template_name='canvas.html'),            name='canvas'),
    path('learn.html',            TemplateView.as_view(template_name='learn.html'),            name='learn'),
    path('subject-hub.html',      TemplateView.as_view(template_name='subject-hub.html'),      name='subject_hub'),
    path('landing.html',          TemplateView.as_view(template_name='landing.html'),          name='landing'),
    path('canvas.html',            TemplateView.as_view(template_name='canvas.html'),            name='canvas'),
    path('pbl.html',              TemplateView.as_view(template_name='pbl.html'),              name='pbl'),
]
