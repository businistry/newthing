## income_streams/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class IncomeStream(models.Model):
    """
    Model representing different types of income streams available for investment.
    """
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    min_investment = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    expected_return = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def create_stream(self):
        self.save()

    def update_stream(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

    def delete_stream(self):
        self.delete()

class UserIncomeStream(models.Model):
    """
    Model representing a user's investment in a specific income stream.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='income_streams')
    income_stream = models.ForeignKey(IncomeStream, on_delete=models.CASCADE, related_name='user_investments')
    invested_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    investment_date = models.DateTimeField(auto_now_add=True)
    auto_reinvest = models.BooleanField(default=False)
    last_earning_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s investment in {self.income_stream.name}"

    def invest(self, amount):
        self.invested_amount += amount
        self.save()

    def withdraw(self, amount):
        if amount <= self.invested_amount:
            self.invested_amount -= amount
            self.save()
            return True
        return False

    def toggle_auto_reinvest(self):
        self.auto_reinvest = not self.auto_reinvest
        self.save()

class Earnings(models.Model):
    """
    Model representing earnings from a user's income stream investment.
    """
    user_income_stream = models.ForeignKey(UserIncomeStream, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    earning_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Earnings for {self.user_income_stream} on {self.earning_date}"

    def record_earning(self):
        self.save()
        self.user_income_stream.last_earning_update = self.earning_date
        self.user_income_stream.save()

    @classmethod
    def get_earnings_by_date_range(cls, user_income_stream, start_date, end_date):
        return cls.objects.filter(
            user_income_stream=user_income_stream,
            earning_date__range=(start_date, end_date)
        )

class IncomeStreamPerformance(models.Model):
    """
    Model for tracking the historical performance of income streams.
    """
    income_stream = models.ForeignKey(IncomeStream, on_delete=models.CASCADE, related_name='performances')
    date = models.DateField()
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_invested = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('income_stream', 'date')

    def __str__(self):
        return f"{self.income_stream.name} performance on {self.date}"

class ReinvestmentLog(models.Model):
    """
    Model for logging reinvestment activities.
    """
    user_income_stream = models.ForeignKey(UserIncomeStream, on_delete=models.CASCADE, related_name='reinvestment_logs')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reinvestment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reinvestment for {self.user_income_stream} on {self.reinvestment_date}"

class WithdrawalRequest(models.Model):
    """
    Model for handling withdrawal requests from users.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    user_income_stream = models.ForeignKey(UserIncomeStream, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Withdrawal request for {self.user_income_stream} - {self.status}"

    def process_request(self, new_status):
        if new_status in ['approved', 'rejected', 'completed']:
            self.status = new_status
            self.processed_date = models.DateTimeField(auto_now=True)
            self.save()
            return True
        return False
