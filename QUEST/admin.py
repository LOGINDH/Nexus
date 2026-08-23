
# Register your models here.
from django.contrib import admin

from .models import User, Quiz, Question, Attempt


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "user_code",
        "name",
        "email",
        "role",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "user_code",
        "name",
        "email",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (

        (
            "Account Information",
            {
                "fields": (
                    "user_code",
                    "name",
                    "email",
                    "password",
                    "role",
                    "is_active",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                )
            }
        ),
    )

    readonly_fields = (
        "created_at",
    )


# ============================================================
# QUIZ ADMIN
# ============================================================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "generation_mode",
        "difficulty",
        "question_count",
        "status",
        "quiz_code",
        "created_by",
        "created_at",
    )

    list_filter = (
        "generation_mode",
        "difficulty",
        "status",
    )

    search_fields = (
        "title",
        "topics",
        "quiz_code",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )


# ============================================================
# QUESTION ADMIN
# ============================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        "quiz",
        "order",
        "question_text",
        "correct_answer",
    )

    list_filter = (
        "quiz",
    )

    search_fields = (
        "question_text",
        "correct_answer",
    )

    ordering = (
        "quiz",
        "order",
    )


# ============================================================
# ATTEMPT ADMIN
# ============================================================

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):

    list_display = (
        "quiz",
        "student",
        "score",
        "total_questions",
        "submitted_at",
    )

    list_filter = (
        "quiz",
        "submitted_at",
    )

    search_fields = (
        "student__user_code",
        "student__name",
        "quiz__title",
    )

    ordering = (
        "-submitted_at",
    )

    readonly_fields = (
        "submitted_at",
    )