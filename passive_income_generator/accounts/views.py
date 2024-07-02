## accounts/views.py

from django.contrib.auth import get_user_model, authenticate, login, logout
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile, UserPreferences, LoginAttempt, PasswordReset, UserActivity
from .serializers import (
    UserSerializer, ProfileSerializer, UserPreferencesSerializer,
    LoginAttemptSerializer, PasswordResetSerializer, UserActivitySerializer,
    UserRegistrationSerializer, ChangePasswordSerializer, UserProfileSerializer
)
from django.core.mail import send_mail
from django.conf import settings
import secrets
from datetime import timedelta

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        Profile.objects.create(user=user)
        UserPreferences.objects.create(user=user)
        UserActivity.objects.create(user=user, activity_type='registration')

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            LoginAttempt.objects.create(user=user, ip_address=request.META.get('REMOTE_ADDR'), was_successful=True)
            UserActivity.objects.create(user=user, activity_type='login')
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            LoginAttempt.objects.create(user=User.objects.get(username=username), ip_address=request.META.get('REMOTE_ADDR'), was_successful=False)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        UserActivity.objects.create(user=request.user, activity_type='logout')
        return Response(status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        UserActivity.objects.create(user=self.request.user, activity_type='profile_update')

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                UserActivity.objects.create(user=user, activity_type='password_change')
                return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Incorrect old password.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        PasswordReset.objects.create(user=user, token=token, expires_at=expires_at)

        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
        send_mail(
            'Password Reset Request',
            f'Click the following link to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        UserActivity.objects.create(user=user, activity_type='password_reset_request')
        return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        try:
            reset_request = PasswordReset.objects.get(token=token, is_used=False, expires_at__gt=timezone.now())
        except PasswordReset.DoesNotExist:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        user = reset_request.user
        user.set_password(new_password)
        user.save()

        reset_request.is_used = True
        reset_request.save()

        UserActivity.objects.create(user=user, activity_type='password_reset_confirm')
        return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.preferences

    def perform_update(self, serializer):
        serializer.save()
        UserActivity.objects.create(user=self.request.user, activity_type='preferences_update')

class UserActivityListView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by('-timestamp')

class LoginAttemptListView(generics.ListAPIView):
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LoginAttempt.objects.filter(user=self.request.user).order_by('-timestamp')

class DeactivateAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        UserActivity.objects.create(user=user, activity_type='account_deactivation')
        return Response({'message': 'Account deactivated successfully.'}, status=status.HTTP_200_OK)

class ReactivateAccountView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response({'error': 'No inactive account found with this email.'}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = True
        user.save()
        UserActivity.objects.create(user=user, activity_type='account_reactivation')
        return Response({'message': 'Account reactivated successfully.'}, status=status.HTTP_200_OK)
