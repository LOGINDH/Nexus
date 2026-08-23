from django.db import models


# ============================================================
# USER
# ============================================================

class User(models.Model):

    ROLE_CHOICES = (
        ("student", "Student"),
        ("staff", "Staff"),
    )

    user_code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user_code} - {self.name}"


# ============================================================
# QUIZ
# ============================================================

class Quiz(models.Model):

    DIFFICULTY_CHOICES = (
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    )

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("active", "Active"),
        ("closed", "Closed"),
    )

    GENERATION_MODE_CHOICES = (
        ("material", "Material"),
        ("ai", "AI"),
    )

    title = models.CharField(
        max_length=200
    )

    topics = models.TextField()

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES
    )

    question_count = models.PositiveIntegerField()

    generation_mode = models.CharField(
        max_length=20,
        choices=GENERATION_MODE_CHOICES
    )

    reference_file = models.FileField(
        upload_to="materials/",
        null=True,
        blank=True
    )

    extracted_text = models.TextField(
        blank=True
    )

    ai_specification = models.JSONField(
        null=True,
        blank=True
    )

    quiz_code = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_quizzes"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title


# ============================================================
# QUESTION
# ============================================================

class Question(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()

    option_a = models.CharField(
        max_length=500
    )

    option_b = models.CharField(
        max_length=500
    )

    option_c = models.CharField(
        max_length=500
    )

    option_d = models.CharField(
        max_length=500
    )

    correct_answer = models.CharField(
        max_length=500
    )

    explanation = models.TextField(
        blank=True
    )

    order = models.PositiveIntegerField()

    def __str__(self):
        return self.question_text[:100]


# ============================================================
# QUIZ ATTEMPT
# ============================================================

class Attempt(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    answers = models.JSONField(
        default=dict
    )

    score = models.PositiveIntegerField(
        default=0
    )

    total_questions = models.PositiveIntegerField(
        default=0
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.student.name} - "
            f"{self.quiz.title}"
        )