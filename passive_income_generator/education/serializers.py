## education/serializers.py

from rest_framework import serializers
from .models import (
    EducationResource, ResourceCategory, UserProgress, ResourceRating,
    LearningPath, LearningPathItem, Quiz, QuizQuestion, QuizAnswer,
    UserQuizAttempt, UserQuizAnswer
)
from django.contrib.auth import get_user_model

User = get_user_model()

class EducationResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationResource
        fields = ['id', 'title', 'slug', 'content', 'resource_type', 'publication_date',
                  'last_updated', 'author', 'difficulty_level', 'estimated_reading_time',
                  'is_published', 'view_count']
        read_only_fields = ['slug', 'publication_date', 'last_updated', 'view_count']

    def create(self, validated_data):
        return EducationResource.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = ['id', 'name', 'description', 'resources']

class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['id', 'user', 'resource', 'completed', 'last_accessed', 'completion_date']
        read_only_fields = ['last_accessed', 'completion_date']

class ResourceRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceRating
        fields = ['id', 'user', 'resource', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class LearningPathItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPathItem
        fields = ['id', 'learning_path', 'resource', 'order']

class LearningPathSerializer(serializers.ModelSerializer):
    resources = LearningPathItemSerializer(source='learningpathitem_set', many=True, read_only=True)

    class Meta:
        model = LearningPath
        fields = ['id', 'title', 'description', 'resources', 'created_by', 'created_at', 'updated_at', 'is_published']
        read_only_fields = ['created_at', 'updated_at']

class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id', 'answer_text', 'is_correct']

class QuizQuestionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'order', 'answers']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'resource', 'title', 'description', 'pass_score', 'questions']

class UserQuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizAnswer
        fields = ['id', 'attempt', 'question', 'answer']

class UserQuizAttemptSerializer(serializers.ModelSerializer):
    answers = UserQuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = UserQuizAttempt
        fields = ['id', 'user', 'quiz', 'score', 'passed', 'attempt_date', 'answers']
        read_only_fields = ['score', 'passed', 'attempt_date']

class EducationResourceDetailSerializer(EducationResourceSerializer):
    categories = ResourceCategorySerializer(many=True, read_only=True)
    ratings = ResourceRatingSerializer(many=True, read_only=True)
    quiz = QuizSerializer(read_only=True)

    class Meta(EducationResourceSerializer.Meta):
        fields = EducationResourceSerializer.Meta.fields + ['categories', 'ratings', 'quiz']

class UserEducationProgressSerializer(serializers.ModelSerializer):
    progress = UserProgressSerializer(many=True, read_only=True)
    quiz_attempts = UserQuizAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'progress', 'quiz_attempts']
        read_only_fields = ['username']

class LearningPathDetailSerializer(LearningPathSerializer):
    resources = serializers.SerializerMethodField()

    class Meta(LearningPathSerializer.Meta):
        fields = LearningPathSerializer.Meta.fields

    def get_resources(self, obj):
        items = LearningPathItem.objects.filter(learning_path=obj).order_by('order')
        return [EducationResourceSerializer(item.resource).data for item in items]

class QuizSubmissionSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )

    def validate_quiz_id(self, value):
        try:
            return Quiz.objects.get(pk=value)
        except Quiz.DoesNotExist:
            raise serializers.ValidationError("Invalid quiz ID")

    def validate_answers(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Answers must be a list")
        for answer in value:
            if not isinstance(answer, dict) or 'question_id' not in answer or 'answer_id' not in answer:
                raise serializers.ValidationError("Each answer must be a dictionary with 'question_id' and 'answer_id'")
        return value

class ResourceRecommendationSerializer(serializers.Serializer):
    resource = EducationResourceSerializer(read_only=True)
    relevance_score = serializers.FloatField()

class UserLearningPathProgressSerializer(serializers.Serializer):
    learning_path = LearningPathSerializer(read_only=True)
    completed_resources = serializers.IntegerField()
    total_resources = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
