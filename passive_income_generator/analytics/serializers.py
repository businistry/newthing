## analytics/serializers.py

from rest_framework import serializers
from .models import Analytics, PredictedEarnings, PerformanceMetric, RiskAssessment, IncomeStreamAnalytics, AnalyticsSnapshot
from income_streams.models import UserIncomeStream
from django.contrib.auth import get_user_model

User = get_user_model()

class AnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analytics
        fields = ['id', 'user', 'last_report_date', 'total_investments', 'total_earnings', 'overall_roi']
        read_only_fields = ['user', 'last_report_date']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Analytics.objects.create(**validated_data)

class PredictedEarningsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictedEarnings
        fields = ['id', 'analytics', 'date', 'amount']
        read_only_fields = ['analytics']

    def create(self, validated_data):
        validated_data['analytics'] = self.context['request'].user.analytics
        return PredictedEarnings.objects.create(**validated_data)

class PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = ['id', 'analytics', 'metric_type', 'value', 'date']
        read_only_fields = ['analytics', 'date']

    def create(self, validated_data):
        validated_data['analytics'] = self.context['request'].user.analytics
        return PerformanceMetric.objects.create(**validated_data)

class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = ['id', 'analytics', 'risk_level', 'assessment_date', 'notes']
        read_only_fields = ['analytics', 'assessment_date']

    def create(self, validated_data):
        validated_data['analytics'] = self.context['request'].user.analytics
        return RiskAssessment.objects.create(**validated_data)

class IncomeStreamAnalyticsSerializer(serializers.ModelSerializer):
    user_income_stream = serializers.PrimaryKeyRelatedField(queryset=UserIncomeStream.objects.all())

    class Meta:
        model = IncomeStreamAnalytics
        fields = ['id', 'analytics', 'user_income_stream', 'total_earnings', 'roi', 'last_updated']
        read_only_fields = ['analytics', 'last_updated']

    def create(self, validated_data):
        validated_data['analytics'] = self.context['request'].user.analytics
        return IncomeStreamAnalytics.objects.create(**validated_data)

class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsSnapshot
        fields = ['id', 'analytics', 'snapshot_date', 'total_investments', 'total_earnings', 'overall_roi']
        read_only_fields = ['analytics', 'snapshot_date']

    def create(self, validated_data):
        validated_data['analytics'] = self.context['request'].user.analytics
        return AnalyticsSnapshot.objects.create(**validated_data)

class UserAnalyticsSerializer(serializers.ModelSerializer):
    analytics = AnalyticsSerializer(read_only=True)
    predicted_earnings = PredictedEarningsSerializer(many=True, read_only=True)
    performance_metrics = PerformanceMetricSerializer(many=True, read_only=True)
    risk_assessments = RiskAssessmentSerializer(many=True, read_only=True)
    income_stream_analytics = IncomeStreamAnalyticsSerializer(many=True, read_only=True)
    snapshots = AnalyticsSnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'analytics', 'predicted_earnings', 'performance_metrics', 'risk_assessments', 'income_stream_analytics', 'snapshots']
        read_only_fields = ['username']

class AnalyticsReportSerializer(serializers.Serializer):
    total_investments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    overall_roi = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    predicted_earnings = PredictedEarningsSerializer(many=True, read_only=True)
    performance_metrics = PerformanceMetricSerializer(many=True, read_only=True)
    risk_assessment = RiskAssessmentSerializer(read_only=True)
    income_stream_analytics = IncomeStreamAnalyticsSerializer(many=True, read_only=True)

class AnalyticsPredictionSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    prediction_type = serializers.ChoiceField(choices=['linear', 'exponential'], default='linear')

class RiskAssessmentRequestSerializer(serializers.Serializer):
    investment_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    income_streams = serializers.ListField(child=serializers.IntegerField())
    time_horizon = serializers.IntegerField(min_value=1, help_text="Investment time horizon in months")
