from django.urls import path
from .views import RegisterView, UserDetailView, CustomLoginView, LogoutView, get_csrf_token

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('csrf/', get_csrf_token, name='csrf'),
    path('me/', UserDetailView.as_view(), name='me'),
]
