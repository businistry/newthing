## analytics/models.py

from django.db import models
from django.conf import settings
from income_streams.models import UserIncomeStream
from django.core.validators import MinValueValidator, MaxValueValidator

class Analytics(models.Model):
    """
    Model for storing user analytics data.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics')
    last_report_date = models.DateTimeField(null=True, blank=True)
    total_investments = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    overall_roi = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"Analytics for {self.user.username}"

    def generate_report(self):
        # Update total investments and earnings
        user_income_streams = UserIncomeStream.objects.filter(user=self.user)
        self.total_investments = sum(stream.invested_amount for stream in user_income_streams)
        self.total_earnings = sum(stream.earnings.aggregate(models.Sum('amount'))['amount__sum'] or 0 for stream in user_income_streams)

        # Calculate overall ROI
        if self.total_investments > 0:
            self.overall_roi = (self.total_earnings / self.total_investments) * 100
        else:
            self.overall_roi = 0

        self.last_report_date = models.DateTimeField(auto_now=True)
        self.save()

    def calculate_roi(self):
        if self.total_investments > 0:
            return (self.total_earnings / self.total_investments) * 100
        return 0

class PredictedEarnings(models.Model):
    """
    Model for storing predicted future earnings.
    """
    analytics = models.ForeignKey(Analytics, on_delete=models.CASCADE, related_name='predicted_earnings')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('analytics', 'date')

    def __str__(self):
        return f"Predicted earnings for {self.analytics.user.username} on {self.date}"

class PerformanceMetric(models.Model):
    """
    Model for storing various performance metrics.
    """
    METRIC_TYPES = [
        ('roi', 'Return on Investment'),
        ('growth_rate', 'Growth Rate'),
        ('volatility', 'Volatility'),
    ]

    analytics = models.ForeignKey(Analytics, on_delete=models.CASCADE, related_name='performance_metrics')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('analytics', 'metric_type', 'date')

    def __str__(self):
        return f"{self.get_metric_type_display()} for {self.analytics.user.username} on {self.date}"

class RiskAssessment(models.Model):
    """
    Model for storing user risk assessments.
    """
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    analytics = models.ForeignKey(Analytics, on_delete=models.CASCADE, related_name='risk_assessments')
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    assessment_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Risk assessment for {self.analytics.user.username} on {self.assessment_date}"

class IncomeStreamAnalytics(models.Model):
    """
    Model for storing analytics specific to each income stream.
    """
    analytics = models.ForeignKey(Analytics, on_delete=models.CASCADE, related_name='income_stream_analytics')
    user_income_stream = models.ForeignKey(UserIncomeStream, on_delete=models.CASCADE, related_name='analytics')
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    roi = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('analytics', 'user_income_stream')

    def __str__(self):
        return f"Analytics for {self.user_income_stream} of {self.analytics.user.username}"

    def update_analytics(self):
        self.total_earnings = self.user_income_stream.earnings.aggregate(models.Sum('amount'))['amount__sum'] or 0
        if self.user_income_stream.invested_amount > 0:
            self.roi = (self.total_earnings / self.user_income_stream.invested_amount) * 100
        else:
            self.roi = 0
        self.save()

class AnalyticsSnapshot(models.Model):
    """
    Model for storing periodic snapshots of user analytics.
    """
    analytics = models.ForeignKey(Analytics, on_delete=models.CASCADE, related_name='snapshots')
    snapshot_date = models.DateTimeField(auto_now_add=True)
    total_investments = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    overall_roi = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"Analytics snapshot for {self.analytics.user.username} on {self.snapshot_date}"

    @classmethod
    def create_snapshot(cls, analytics):
        return cls.objects.create(
            analytics=analytics,
            total_investments=analytics.total_investments,
            total_earnings=analytics.total_earnings,
            overall_roi=analytics.overall_roi
        )
