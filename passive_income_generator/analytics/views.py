## analytics/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Analytics, PredictedEarnings, PerformanceMetric, RiskAssessment, IncomeStreamAnalytics, AnalyticsSnapshot
from .serializers import (
    AnalyticsSerializer, PredictedEarningsSerializer, PerformanceMetricSerializer,
    RiskAssessmentSerializer, IncomeStreamAnalyticsSerializer, AnalyticsSnapshotSerializer,
    UserAnalyticsSerializer, AnalyticsReportSerializer, AnalyticsPredictionSerializer,
    RiskAssessmentRequestSerializer
)
from income_streams.models import UserIncomeStream, IncomeStream
from django.db.models import Sum, F
import numpy as np
from scipy import stats

class AnalyticsRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = AnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Analytics, user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class PredictedEarningsListCreateView(generics.ListCreateAPIView):
    serializer_class = PredictedEarningsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PredictedEarnings.objects.filter(analytics__user=self.request.user)

    def perform_create(self, serializer):
        analytics = get_object_or_404(Analytics, user=self.request.user)
        serializer.save(analytics=analytics)

class PerformanceMetricListCreateView(generics.ListCreateAPIView):
    serializer_class = PerformanceMetricSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PerformanceMetric.objects.filter(analytics__user=self.request.user)

    def perform_create(self, serializer):
        analytics = get_object_or_404(Analytics, user=self.request.user)
        serializer.save(analytics=analytics)

class RiskAssessmentListCreateView(generics.ListCreateAPIView):
    serializer_class = RiskAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RiskAssessment.objects.filter(analytics__user=self.request.user)

    def perform_create(self, serializer):
        analytics = get_object_or_404(Analytics, user=self.request.user)
        serializer.save(analytics=analytics)

class IncomeStreamAnalyticsListCreateView(generics.ListCreateAPIView):
    serializer_class = IncomeStreamAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IncomeStreamAnalytics.objects.filter(analytics__user=self.request.user)

    def perform_create(self, serializer):
        analytics = get_object_or_404(Analytics, user=self.request.user)
        serializer.save(analytics=analytics)

class AnalyticsSnapshotListCreateView(generics.ListCreateAPIView):
    serializer_class = AnalyticsSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AnalyticsSnapshot.objects.filter(analytics__user=self.request.user)

    def perform_create(self, serializer):
        analytics = get_object_or_404(Analytics, user=self.request.user)
        serializer.save(analytics=analytics)

class UserAnalyticsView(generics.RetrieveAPIView):
    serializer_class = UserAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class GenerateAnalyticsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        analytics = get_object_or_404(Analytics, user=request.user)
        analytics.generate_report()

        report_data = {
            'total_investments': analytics.total_investments,
            'total_earnings': analytics.total_earnings,
            'overall_roi': analytics.overall_roi,
            'predicted_earnings': PredictedEarnings.objects.filter(analytics=analytics),
            'performance_metrics': PerformanceMetric.objects.filter(analytics=analytics),
            'risk_assessment': RiskAssessment.objects.filter(analytics=analytics).last(),
            'income_stream_analytics': IncomeStreamAnalytics.objects.filter(analytics=analytics),
        }

        serializer = AnalyticsReportSerializer(report_data)
        return Response(serializer.data)

class PredictFutureEarningsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AnalyticsPredictionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        prediction_type = serializer.validated_data['prediction_type']

        analytics = get_object_or_404(Analytics, user=request.user)
        historical_data = AnalyticsSnapshot.objects.filter(
            analytics=analytics,
            snapshot_date__lte=start_date
        ).order_by('snapshot_date')

        if not historical_data:
            return Response({"error": "Insufficient historical data for prediction."}, status=status.HTTP_400_BAD_REQUEST)

        dates = [(snapshot.snapshot_date - historical_data[0].snapshot_date).days for snapshot in historical_data]
        earnings = [float(snapshot.total_earnings) for snapshot in historical_data]

        if prediction_type == 'linear':
            slope, intercept, _, _, _ = stats.linregress(dates, earnings)
            predict_earnings = lambda x: max(slope * x + intercept, 0)  # Ensure non-negative predictions
        else:  # exponential
            # Add a small positive value to handle zero or negative earnings
            adjusted_earnings = [max(e, 0.01) for e in earnings]
            log_earnings = np.log(adjusted_earnings)
            slope, intercept, _, _, _ = stats.linregress(dates, log_earnings)
            predict_earnings = lambda x: max(np.exp(slope * x + intercept), 0)  # Ensure non-negative predictions

        prediction_days = (end_date - start_date).days
        predicted_earnings = [predict_earnings(day) for day in range(len(dates), len(dates) + prediction_days)]

        prediction_dates = [start_date + timedelta(days=i) for i in range(prediction_days)]
        predictions = [
            {"date": date, "amount": Decimal(str(round(amount, 2)))}
            for date, amount in zip(prediction_dates, predicted_earnings)
        ]

        return Response(predictions)

class PerformRiskAssessmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RiskAssessmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        investment_amount = serializer.validated_data['investment_amount']
        income_stream_ids = serializer.validated_data['income_streams']
        time_horizon = serializer.validated_data['time_horizon']

        income_streams = IncomeStream.objects.filter(id__in=income_stream_ids)
        
        if not income_streams:
            return Response({"error": "No valid income streams provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate weighted average risk
        risk_levels = {'low': 1, 'medium': 2, 'high': 3}
        weighted_risk = sum(stream.expected_return * risk_levels[stream.risk_level] for stream in income_streams)
        total_weight = sum(stream.expected_return for stream in income_streams)

        average_risk = weighted_risk / total_weight if total_weight > 0 else 0

        # Determine overall risk level
        if average_risk < 1.5:
            risk_level = 'low'
        elif average_risk < 2.5:
            risk_level = 'medium'
        else:
            risk_level = 'high'

        # Create risk assessment
        analytics = get_object_or_404(Analytics, user=request.user)
        risk_assessment = RiskAssessment.objects.create(
            analytics=analytics,
            risk_level=risk_level,
            notes=f"Based on {len(income_streams)} income streams over {time_horizon} months with {investment_amount} investment."
        )

        return Response({
            "risk_level": risk_level,
            "assessment_id": risk_assessment.id,
            "notes": risk_assessment.notes
        })

class AnalyticsSnapshotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        analytics = get_object_or_404(Analytics, user=request.user)
        snapshot = AnalyticsSnapshot.create_snapshot(analytics)
        serializer = AnalyticsSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class IncomeStreamAnalyticsUpdateView(generics.UpdateAPIView):
    serializer_class = IncomeStreamAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IncomeStreamAnalytics.objects.filter(analytics__user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.update_analytics()

class AnalyticsOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        analytics = get_object_or_404(Analytics, user=request.user)
        
        income_streams = UserIncomeStream.objects.filter(user=request.user)
        total_invested = income_streams.aggregate(total=Sum('invested_amount'))['total'] or Decimal('0')
        total_earnings = income_streams.aggregate(total=Sum('earnings__amount'))['total'] or Decimal('0')

        overall_roi = (total_earnings / total_invested * 100) if total_invested > 0 else Decimal('0')

        return Response({
            "total_invested": total_invested,
            "total_earnings": total_earnings,
            "overall_roi": overall_roi,
            "active_income_streams": income_streams.count(),
            "last_report_date": analytics.last_report_date
        })
