## income_streams/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from .models import IncomeStream, UserIncomeStream, Earnings, IncomeStreamPerformance, ReinvestmentLog, WithdrawalRequest
from .serializers import (
    IncomeStreamSerializer, UserIncomeStreamSerializer, EarningsSerializer,
    IncomeStreamPerformanceSerializer, ReinvestmentLogSerializer,
    WithdrawalRequestSerializer, UserIncomeStreamDetailSerializer,
    IncomeStreamDetailSerializer
)

class IncomeStreamListCreateView(generics.ListCreateAPIView):
    queryset = IncomeStream.objects.all()
    serializer_class = IncomeStreamSerializer
    permission_classes = [permissions.IsAuthenticated]

class IncomeStreamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IncomeStream.objects.all()
    serializer_class = IncomeStreamDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserIncomeStreamListCreateView(generics.ListCreateAPIView):
    serializer_class = UserIncomeStreamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserIncomeStream.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserIncomeStreamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserIncomeStreamDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserIncomeStream.objects.filter(user=self.request.user)

class EarningsListCreateView(generics.ListCreateAPIView):
    serializer_class = EarningsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Earnings.objects.filter(user_income_stream__user=self.request.user)

    def perform_create(self, serializer):
        user_income_stream = serializer.validated_data['user_income_stream']
        if user_income_stream.user != self.request.user:
            raise serializers.ValidationError("You can only create earnings for your own income streams.")
        serializer.save()

class IncomeStreamPerformanceListView(generics.ListAPIView):
    serializer_class = IncomeStreamPerformanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        income_stream_id = self.kwargs.get('income_stream_id')
        return IncomeStreamPerformance.objects.filter(income_stream_id=income_stream_id)

class ReinvestmentLogListCreateView(generics.ListCreateAPIView):
    serializer_class = ReinvestmentLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReinvestmentLog.objects.filter(user_income_stream__user=self.request.user)

    def perform_create(self, serializer):
        user_income_stream = serializer.validated_data['user_income_stream']
        if user_income_stream.user != self.request.user:
            raise serializers.ValidationError("You can only create reinvestment logs for your own income streams.")
        serializer.save()

class WithdrawalRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user_income_stream__user=self.request.user)

    def perform_create(self, serializer):
        user_income_stream = serializer.validated_data['user_income_stream']
        amount = serializer.validated_data['amount']
        if user_income_stream.user != self.request.user:
            raise serializers.ValidationError("You can only create withdrawal requests for your own income streams.")
        if amount > user_income_stream.invested_amount:
            raise serializers.ValidationError("Insufficient funds for withdrawal.")
        serializer.save()

class WithdrawalRequestProcessView(generics.UpdateAPIView):
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        withdrawal_request = self.get_object()
        new_status = request.data.get('status')
        if withdrawal_request.process_request(new_status):
            return Response({"message": f"Withdrawal request status updated to {new_status}."})
        return Response({"error": "Invalid status update."}, status=status.HTTP_400_BAD_REQUEST)

class UserIncomeStreamInvestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user_income_stream = get_object_or_404(UserIncomeStream, pk=pk, user=request.user)
        amount = request.data.get('amount')
        if not amount:
            return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = Decimal(amount)
        except InvalidOperation:
            return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
        user_income_stream.invest(amount)
        return Response({"message": f"Successfully invested {amount} in {user_income_stream.income_stream.name}."})

class UserIncomeStreamWithdrawView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user_income_stream = get_object_or_404(UserIncomeStream, pk=pk, user=request.user)
        amount = request.data.get('amount')
        if not amount:
            return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = Decimal(amount)
        except InvalidOperation:
            return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
        if user_income_stream.withdraw(amount):
            return Response({"message": f"Successfully withdrew {amount} from {user_income_stream.income_stream.name}."})
        return Response({"error": "Insufficient funds for withdrawal."}, status=status.HTTP_400_BAD_REQUEST)

class UserIncomeStreamToggleAutoReinvestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user_income_stream = get_object_or_404(UserIncomeStream, pk=pk, user=request.user)
        user_income_stream.toggle_auto_reinvest()
        return Response({
            "message": f"Auto-reinvest toggled for {user_income_stream.income_stream.name}.",
            "auto_reinvest": user_income_stream.auto_reinvest
        })

class UserEarningsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date())
        
        earnings = Earnings.objects.filter(
            user_income_stream__user=request.user,
            earning_date__range=(start_date, end_date)
        ).aggregate(total_earnings=Sum('amount'))

        return Response({
            "total_earnings": earnings['total_earnings'] or 0,
            "start_date": start_date,
            "end_date": end_date
        })

class IncomeStreamRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        risk_tolerance = request.user.profile.risk_tolerance
        recommended_streams = IncomeStream.objects.filter(risk_level=risk_tolerance)
        serializer = IncomeStreamSerializer(recommended_streams, many=True)
        return Response(serializer.data)
