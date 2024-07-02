## income_streams/serializers.py

from rest_framework import serializers
from .models import IncomeStream, UserIncomeStream, Earnings, IncomeStreamPerformance, ReinvestmentLog, WithdrawalRequest
from django.contrib.auth import get_user_model

User = get_user_model()

class IncomeStreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeStream
        fields = ['id', 'name', 'description', 'min_investment', 'expected_return', 'risk_level', 'created_at', 'updated_at']

    def create(self, validated_data):
        return IncomeStream.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserIncomeStreamSerializer(serializers.ModelSerializer):
    income_stream = IncomeStreamSerializer(read_only=True)
    income_stream_id = serializers.PrimaryKeyRelatedField(
        queryset=IncomeStream.objects.all(),
        source='income_stream',
        write_only=True
    )

    class Meta:
        model = UserIncomeStream
        fields = ['id', 'user', 'income_stream', 'income_stream_id', 'invested_amount', 'investment_date', 'auto_reinvest', 'last_earning_update']
        read_only_fields = ['user', 'investment_date', 'last_earning_update']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return UserIncomeStream.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class EarningsSerializer(serializers.ModelSerializer):
    user_income_stream = UserIncomeStreamSerializer(read_only=True)

    class Meta:
        model = Earnings
        fields = ['id', 'user_income_stream', 'amount', 'earning_date']
        read_only_fields = ['earning_date']

    def create(self, validated_data):
        return Earnings.objects.create(**validated_data)

class IncomeStreamPerformanceSerializer(serializers.ModelSerializer):
    income_stream = IncomeStreamSerializer(read_only=True)

    class Meta:
        model = IncomeStreamPerformance
        fields = ['id', 'income_stream', 'date', 'return_rate', 'total_invested', 'total_earnings']

    def create(self, validated_data):
        return IncomeStreamPerformance.objects.create(**validated_data)

class ReinvestmentLogSerializer(serializers.ModelSerializer):
    user_income_stream = UserIncomeStreamSerializer(read_only=True)

    class Meta:
        model = ReinvestmentLog
        fields = ['id', 'user_income_stream', 'amount', 'reinvestment_date']
        read_only_fields = ['reinvestment_date']

    def create(self, validated_data):
        return ReinvestmentLog.objects.create(**validated_data)

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user_income_stream = UserIncomeStreamSerializer(read_only=True)
    user_income_stream_id = serializers.PrimaryKeyRelatedField(
        queryset=UserIncomeStream.objects.all(),
        source='user_income_stream',
        write_only=True
    )

    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'user_income_stream', 'user_income_stream_id', 'amount', 'request_date', 'status', 'processed_date']
        read_only_fields = ['request_date', 'status', 'processed_date']

    def create(self, validated_data):
        return WithdrawalRequest.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserIncomeStreamDetailSerializer(serializers.ModelSerializer):
    income_stream = IncomeStreamSerializer(read_only=True)
    earnings = EarningsSerializer(many=True, read_only=True)
    reinvestment_logs = ReinvestmentLogSerializer(many=True, read_only=True)
    withdrawal_requests = WithdrawalRequestSerializer(many=True, read_only=True)

    class Meta:
        model = UserIncomeStream
        fields = ['id', 'user', 'income_stream', 'invested_amount', 'investment_date', 'auto_reinvest', 'last_earning_update', 'earnings', 'reinvestment_logs', 'withdrawal_requests']
        read_only_fields = ['user', 'investment_date', 'last_earning_update']

class IncomeStreamDetailSerializer(serializers.ModelSerializer):
    user_investments = UserIncomeStreamSerializer(many=True, read_only=True)
    performances = IncomeStreamPerformanceSerializer(many=True, read_only=True)

    class Meta:
        model = IncomeStream
        fields = ['id', 'name', 'description', 'min_investment', 'expected_return', 'risk_level', 'created_at', 'updated_at', 'user_investments', 'performances']
