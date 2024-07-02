## education/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify

class EducationResource(models.Model):
    """
    Model representing educational resources.
    """
    RESOURCE_TYPES = [
        ('article', 'Article'),
        ('video', 'Video'),
        ('webinar', 'Webinar'),
        ('ebook', 'E-Book'),
        ('quiz', 'Quiz'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='article')
    publication_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='authored_resources')
    difficulty_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        help_text="1 (Beginner) to 5 (Expert)"
    )
    estimated_reading_time = models.PositiveIntegerField(
        default=5,
        help_text="Estimated reading time in minutes"
    )
    is_published = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def create_resource(self):
        self.save()

    def update_resource(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

    def delete_resource(self):
        self.delete()

    def increment_view_count(self):
        self.view_count += 1
        self.save()

class ResourceCategory(models.Model):
    """
    Model for categorizing educational resources.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    resources = models.ManyToManyField(EducationResource, related_name='categories')

    def __str__(self):
        return self.name

class UserProgress(models.Model):
    """
    Model to track user progress through educational resources.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='education_progress')
    resource = models.ForeignKey(EducationResource, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'resource')

    def __str__(self):
        return f"{self.user.username}'s progress on {self.resource.title}"

    def mark_completed(self):
        from django.utils import timezone
        self.completed = True
        self.completion_date = timezone.now()
        self.save()

class ResourceRating(models.Model):
    """
    Model for users to rate educational resources.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(EducationResource, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'resource')

    def __str__(self):
        return f"{self.user.username}'s rating for {self.resource.title}"

class LearningPath(models.Model):
    """
    Model representing a curated learning path of educational resources.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    resources = models.ManyToManyField(EducationResource, through='LearningPathItem')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_learning_paths')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class LearningPathItem(models.Model):
    """
    Model representing an item in a learning path, allowing for ordering of resources.
    """
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    resource = models.ForeignKey(EducationResource, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('learning_path', 'resource')

    def __str__(self):
        return f"{self.resource.title} in {self.learning_path.title}"

class Quiz(models.Model):
    """
    Model representing a quiz associated with an educational resource.
    """
    resource = models.OneToOneField(EducationResource, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pass_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Passing score percentage"
    )

    def __str__(self):
        return f"Quiz for {self.resource.title}"

class QuizQuestion(models.Model):
    """
    Model representing a question in a quiz.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order} of {self.quiz}"

class QuizAnswer(models.Model):
    """
    Model representing an answer to a quiz question.
    """
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer to {self.question}"

class UserQuizAttempt(models.Model):
    """
    Model to track user attempts at quizzes.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    passed = models.BooleanField(default=False)
    attempt_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s attempt at {self.quiz}"

    def calculate_score(self):
        total_questions = self.quiz.questions.count()
        correct_answers = self.answers.filter(answer__is_correct=True).count()
        self.score = (correct_answers / total_questions) * 100
        self.passed = self.score >= self.quiz.pass_score
        self.save()

class UserQuizAnswer(models.Model):
    """
    Model to store user's answers to quiz questions.
    """
    attempt = models.ForeignKey(UserQuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer = models.ForeignKey(QuizAnswer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"{self.attempt.user.username}'s answer to {self.question}"
