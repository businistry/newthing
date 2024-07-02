## accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, UserPreferences, LoginAttempt, PasswordReset, UserActivity

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_active', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'risk_tolerance', 'total_earnings']

    def update(self, instance, validated_data):
        instance.risk_tolerance = validated_data.get('risk_tolerance', instance.risk_tolerance)
        instance.total_earnings = validated_data.get('total_earnings', instance.total_earnings)
        instance.save()
        return instance

class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = ['id', 'user', 'receive_notifications', 'notification_frequency', 'preferred_currency']

class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = ['id', 'user', 'timestamp', 'ip_address', 'was_successful']

class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = ['id', 'user', 'token', 'created_at', 'expires_at', 'is_used']

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity_type', 'timestamp', 'details']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        UserPreferences.objects.create(user=user)
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    preferences = UserPreferencesSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'preferences']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        preferences_data = validated_data.pop('preferences', {})

        instance = super().update(instance, validated_data)

        if profile_data:
            profile_serializer = ProfileSerializer(instance.profile, data=profile_data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()

        if preferences_data:
            preferences_serializer = UserPreferencesSerializer(instance.preferences, data=preferences_data, partial=True)
            if preferences_serializer.is_valid():
                preferences_serializer.save()

        return instance
