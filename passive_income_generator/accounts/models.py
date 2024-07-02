## accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    """
    User profile model containing additional user information.
    """
    RISK_TOLERANCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    risk_tolerance = models.CharField(max_length=10, choices=RISK_TOLERANCE_CHOICES, default='medium')
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def update_profile(self, risk_tolerance=None):
        """
        Update the user's profile information.
        """
        if risk_tolerance:
            self.risk_tolerance = risk_tolerance
        self.save()

    def get_total_earnings(self):
        """
        Calculate and return the user's total earnings.
        """
        return self.total_earnings

    def __str__(self):
        return f"{self.user.username}'s Profile"

class UserPreferences(models.Model):
    """
    User preferences model for customizing user experience.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    receive_notifications = models.BooleanField(default=True)
    notification_frequency = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="Number of days between notifications (1-7)"
    )
    preferred_currency = models.CharField(max_length=3, default='USD')

    def __str__(self):
        return f"{self.user.username}'s Preferences"

class LoginAttempt(models.Model):
    """
    Model to track user login attempts for security purposes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    was_successful = models.BooleanField(default=False)

    def __str__(self):
        return f"Login attempt for {self.user.username} at {self.timestamp}"

class PasswordReset(models.Model):
    """
    Model to handle password reset requests.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Password reset for {self.user.username}"

class UserActivity(models.Model):
    """
    Model to track user activity for analytics purposes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"
