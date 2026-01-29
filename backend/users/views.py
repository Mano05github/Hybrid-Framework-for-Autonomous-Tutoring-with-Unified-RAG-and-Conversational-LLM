from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CustomLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        login_id = request.data.get('login_id')
        password = request.data.get('password')

        if not login_id or not password:
            return Response({'error': 'Please provide login credential (ID/Username/Email) and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if login_id is email, username, or student_id (case-insensitive)
        user = User.objects.filter(
            Q(username__iexact=login_id) | 
            Q(email__iexact=login_id) |
            Q(student_id__iexact=login_id)
        ).first()

        if user is None:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate
        if not user.check_password(password):
             return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Use Django's login for session-based auth
        login(request, user)
        
        serializer = UserSerializer(user)
        return Response({
            'message': 'Login successful',
            'user': serializer.data
        })

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})

class UserDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

@ensure_csrf_cookie
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE', '')})
