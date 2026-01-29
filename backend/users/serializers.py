import re
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_student', 'is_tutor', 'student_id')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'is_student')

    def validate_password(self, value):
        # Minimum 8 characters with at least one letter and one number
        # Special characters are optional for better UX
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        
        has_letter = any(c.isalpha() for c in value)
        has_number = any(c.isdigit() for c in value)
        
        if not has_letter:
            raise serializers.ValidationError(
                "Password must contain at least one letter."
            )
        
        if not has_number:
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        
        return value

    def validate_username(self, value):
        # Username must be at least 3 characters
        # Allow alphanumeric and common special characters
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        # Allow letters, numbers, and common special chars: @._-
        if not re.match(r'^[a-zA-Z0-9@._-]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, and special characters (@, ., _, -)."
            )
        
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password') # Remove confirm_password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            is_student=validated_data.get('is_student', True)
        )
        return user
