## education/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q
from django.utils import timezone
from .models import (
    EducationResource, ResourceCategory, UserProgress, ResourceRating,
    LearningPath, LearningPathItem, Quiz, QuizQuestion, QuizAnswer,
    UserQuizAttempt, UserQuizAnswer
)
from .serializers import (
    EducationResourceSerializer, ResourceCategorySerializer, UserProgressSerializer,
    ResourceRatingSerializer, LearningPathSerializer, QuizSerializer,
    UserQuizAttemptSerializer, EducationResourceDetailSerializer,
    UserEducationProgressSerializer, LearningPathDetailSerializer,
    QuizSubmissionSerializer, ResourceRecommendationSerializer,
    UserLearningPathProgressSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()

class EducationResourceListCreateView(generics.ListCreateAPIView):
    queryset = EducationResource.objects.all()
    serializer_class = EducationResourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class EducationResourceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EducationResource.objects.all()
    serializer_class = EducationResourceDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class ResourceCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserProgressListCreateView(generics.ListCreateAPIView):
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ResourceRatingListCreateView(generics.ListCreateAPIView):
    serializer_class = ResourceRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        resource_id = self.kwargs.get('resource_id')
        return ResourceRating.objects.filter(resource_id=resource_id)

    def perform_create(self, serializer):
        resource_id = self.kwargs.get('resource_id')
        resource = get_object_or_404(EducationResource, id=resource_id)
        serializer.save(user=self.request.user, resource=resource)

class LearningPathListCreateView(generics.ListCreateAPIView):
    queryset = LearningPath.objects.all()
    serializer_class = LearningPathSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class LearningPathRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LearningPath.objects.all()
    serializer_class = LearningPathDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class QuizRetrieveView(generics.RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

class QuizSubmissionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = QuizSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quiz = serializer.validated_data['quiz_id']
        answers = serializer.validated_data['answers']

        quiz_attempt = UserQuizAttempt.objects.create(user=request.user, quiz=quiz)

        for answer in answers:
            question = get_object_or_404(QuizQuestion, id=answer['question_id'], quiz=quiz)
            selected_answer = get_object_or_404(QuizAnswer, id=answer['answer_id'], question=question)
            UserQuizAnswer.objects.create(attempt=quiz_attempt, question=question, answer=selected_answer)

        quiz_attempt.calculate_score()

        return Response({
            'score': quiz_attempt.score,
            'passed': quiz_attempt.passed
        }, status=status.HTTP_201_CREATED)

class UserEducationProgressView(generics.RetrieveAPIView):
    serializer_class = UserEducationProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class MarkResourceCompletedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, resource_id):
        resource = get_object_or_404(EducationResource, id=resource_id)
        progress, created = UserProgress.objects.get_or_create(user=request.user, resource=resource)
        progress.mark_completed()
        return Response({'status': 'Resource marked as completed'}, status=status.HTTP_200_OK)

class ResourceRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        completed_resources = UserProgress.objects.filter(user=user, completed=True).values_list('resource', flat=True)
        
        # Get resources not completed by the user
        recommendations = EducationResource.objects.exclude(id__in=completed_resources)
        
        # Apply some recommendation logic (e.g., based on user's interests, difficulty level, etc.)
        recommendations = recommendations.annotate(
            avg_rating=Avg('ratings__rating'),
            relevance_score=Count('ratings') + Count('categories')
        ).order_by('-relevance_score', '-avg_rating')[:5]

        serializer = ResourceRecommendationSerializer(
            [{'resource': r, 'relevance_score': r.relevance_score} for r in recommendations],
            many=True
        )
        return Response(serializer.data)

class UserLearningPathProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, learning_path_id):
        learning_path = get_object_or_404(LearningPath, id=learning_path_id)
        user = request.user

        total_resources = learning_path.resources.count()
        completed_resources = UserProgress.objects.filter(
            user=user,
            resource__in=learning_path.resources.all(),
            completed=True
        ).count()

        progress_percentage = (completed_resources / total_resources) * 100 if total_resources > 0 else 0

        data = {
            'learning_path': learning_path,
            'completed_resources': completed_resources,
            'total_resources': total_resources,
            'progress_percentage': progress_percentage
        }

        serializer = UserLearningPathProgressSerializer(data)
        return Response(serializer.data)

class SearchEducationResourcesView(generics.ListAPIView):
    serializer_class = EducationResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        return EducationResource.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(categories__name__icontains=query)
        ).distinct()

class PopularResourcesView(generics.ListAPIView):
    serializer_class = EducationResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EducationResource.objects.annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        ).order_by('-view_count', '-avg_rating', '-num_ratings')[:10]

class RecentlyAddedResourcesView(generics.ListAPIView):
    serializer_class = EducationResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EducationResource.objects.filter(is_published=True).order_by('-publication_date')[:10]

class UserCompletedResourcesView(generics.ListAPIView):
    serializer_class = EducationResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EducationResource.objects.filter(
            userprogress__user=self.request.user,
            userprogress__completed=True
        )

class ResourcesByCategoryView(generics.ListAPIView):
    serializer_class = EducationResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return EducationResource.objects.filter(categories__id=category_id)

class StartLearningPathView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, learning_path_id):
        learning_path = get_object_or_404(LearningPath, id=learning_path_id)
        first_resource = learning_path.resources.first()
        if first_resource:
            UserProgress.objects.get_or_create(user=request.user, resource=first_resource)
            return Response({'status': 'Started learning path', 'first_resource_id': first_resource.id}, status=status.HTTP_200_OK)
        return Response({'error': 'No resources in this learning path'}, status=status.HTTP_400_BAD_REQUEST)
