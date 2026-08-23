import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (
    User,
    Quiz,
    Question,
    Attempt
)

from .decorators import (
    student_required,
    staff_required
)

from .utils import (
    generate_user_code,
    generate_quiz_code,
    extract_pdf_text
)

from .quiz_generator import (
    generate_questions
)

from .validators import (
    validate_quiz_json
)


# ============================================================
# HOME / API STATUS
# ============================================================
@csrf_exempt
def home(request):

    return JsonResponse({
        "success": True,
        "message": "QUEST API is running.",
        "project": "QUEST",
        "version": "1.0"
    })


# ============================================================
# STUDENT REGISTER
# ============================================================

@csrf_exempt
def student_register(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed."
        }, status=405)

    try:

        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({
            "success": False,
            "message": "Invalid JSON."
        }, status=400)

    name = data.get(
        "name",
        ""
    ).strip()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not name:

        return JsonResponse({
            "success": False,
            "message": "Name is required."
        }, status=400)

    if not email:

        return JsonResponse({
            "success": False,
            "message": "Email is required."
        }, status=400)

    if not password:

        return JsonResponse({
            "success": False,
            "message": "Password is required."
        }, status=400)

    if User.objects.filter(
        email=email
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Email already exists."
        }, status=400)

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    user_code = generate_user_code(
        "student"
    )

    user = User.objects.create(

        user_code=user_code,

        name=name,

        email=email,

        password=password,

        role="student"
    )

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    request.session["user_id"] = user.id

    request.session["role"] = "student"

    request.session["user_code"] = user.user_code

    return JsonResponse({

        "success": True,

        "message": "Student registered successfully.",

        "user": {

            "id": user.id,

            "user_code": user.user_code,

            "name": user.name,

            "email": user.email,

            "role": user.role
        }
    }, status=201)


# ============================================================
# STUDENT LOGIN
# ============================================================

@csrf_exempt
def student_login(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed."
        }, status=405)

    try:

        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({
            "success": False,
            "message": "Invalid JSON."
        }, status=400)

    user_code = str(data.get("user_code") or data.get("username") or data.get("student_id") or "").strip()
    password = str(data.get("password", ""))

    user = User.objects.filter(
        role="student",
        is_active=True
    ).filter(
        user_code__iexact=user_code
    ).first()

    if not user or user.password != password:
        return JsonResponse({
            "success": False,
            "message": "Invalid student credentials."
        }, status=401)

    request.session["user_id"] = user.id
    request.session["role"] = "student"
    request.session["user_code"] = user.user_code

    return JsonResponse({

        "success": True,

        "message": "Student login successful.",

        "user": {

            "id": user.id,

            "user_code": user.user_code,

            "name": user.name,

            "email": user.email,

            "role": user.role
        }
    })


# ============================================================
# STAFF LOGIN
# ============================================================

@csrf_exempt
@api_view(['POST'])
def staff_login(request):

    data = request.data if hasattr(request, 'data') else {}
    if not data and request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}

    user_code = str(data.get("user_code") or data.get("username") or data.get("identity") or data.get("staff_id") or "").strip()
    password = str(data.get("password", ""))

    # Find staff user matching user_code (case-insensitive)
    user = User.objects.filter(
        role="staff",
        is_active=True
    ).filter(
        user_code__iexact=user_code
    ).first()

    if not user or user.password != password:
        return Response({
            "success": False,
            "message": "Invalid staff credentials."
        }, status=status.HTTP_401_UNAUTHORIZED)

    request.session["user_id"] = user.id
    request.session["role"] = "staff"
    request.session["user_code"] = user.user_code

    return Response({
        "success": True,
        "message": "Staff login successful.",
        "user": {
            "id": user.id,
            "user_code": user.user_code,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }, status=status.HTTP_200_OK)


# ============================================================
# LOGOUT
# ============================================================
@csrf_exempt
def logout_view(request):

    request.session.flush()

    return JsonResponse({

        "success": True,

        "message": "Logged out successfully."
    })


# ============================================================
# CURRENT USER
# ============================================================

@csrf_exempt
def current_user(request):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return JsonResponse({

            "success": False,

            "message": "Not logged in."

        }, status=401)

    user = User.objects.filter(
        id=user_id,
        is_active=True
    ).first()

    if not user:

        request.session.flush()

        return JsonResponse({

            "success": False,

            "message": "User session is invalid."

        }, status=401)

    return JsonResponse({

        "success": True,

        "user": {

            "id": user.id,

            "user_code": user.user_code,

            "name": user.name,

            "email": user.email,

            "role": user.role
        }
    })


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@csrf_exempt
@student_required
def student_dashboard(request):

    quizzes = Quiz.objects.filter(
        status="active"
    ).order_by(
        "-created_at"
    )

    attempts = Attempt.objects.filter(
        student=request.current_user
    ).select_related(
        "quiz"
    ).order_by(
        "-submitted_at"
    )

    quiz_data = []

    for quiz in quizzes:

        quiz_data.append({

            "id": quiz.id,

            "title": quiz.title,

            "topics": quiz.topics,

            "difficulty": quiz.difficulty,

            "question_count": quiz.question_count,

            "quiz_code": quiz.quiz_code,

            "created_at": quiz.created_at
        })

    attempt_data = []

    for attempt in attempts:

        percentage = 0

        if attempt.total_questions:

            percentage = round(

                (
                    attempt.score
                    / attempt.total_questions
                ) * 100,

                2
            )

        attempt_data.append({

            "id": attempt.id,

            "quiz_id": attempt.quiz.id,

            "quiz_title": attempt.quiz.title,

            "score": attempt.score,

            "total_questions": (
                attempt.total_questions
            ),

            "percentage": percentage,

            "submitted_at": (
                attempt.submitted_at
            )
        })

    return JsonResponse({

        "success": True,

        "user": {

            "user_code":
                request.current_user.user_code,

            "name":
                request.current_user.name
        },

        "active_quizzes": quiz_data,

        "previous_attempts": attempt_data
    })


# ============================================================
# STAFF DASHBOARD
# ============================================================
@csrf_exempt
@api_view(['GET', 'POST'])
@staff_required
def staff_dashboard(request):

    quizzes = Quiz.objects.filter(
        created_by=request.current_user
    ).order_by("-created_at")

    attempts = Attempt.objects.filter(
        quiz__created_by=request.current_user
    ).select_related("quiz", "student").order_by("-submitted_at")

    total_attempts = attempts.count()
    if total_attempts > 0:
        total_score_sum = sum(
            (attempt.score / attempt.total_questions * 100) if attempt.total_questions else 0 
            for attempt in attempts
        )
        avg_score = round(total_score_sum / total_attempts, 2)
    else:
        avg_score = 0

    quiz_data = []
    for quiz in quizzes:
        quiz_data.append({
            "id": quiz.id,
            "title": quiz.title,
            "topics": quiz.topics,
            "difficulty": quiz.difficulty,
            "question_count": quiz.question_count,
            "generation_mode": quiz.generation_mode,
            "status": quiz.status,
            "quiz_code": quiz.quiz_code,
            "created_at": quiz.created_at,
            "attempt_count": quiz.attempts.count()
        })

    attempt_data = []
    for attempt in attempts:
        percentage = 0
        if attempt.total_questions:
            percentage = round((attempt.score / attempt.total_questions) * 100, 2)
        attempt_data.append({
            "id": attempt.id,
            "quiz_id": attempt.quiz.id,
            "quiz_title": attempt.quiz.title,
            "student_name": attempt.student.name if attempt.student else "Student",
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "percentage": percentage,
            "submitted_at": attempt.submitted_at
        })

    return Response({
        "success": True,
        "total_quizzes": quizzes.count(),
        "active_quizzes": quizzes.filter(status="active").count(),
        "total_attempts": total_attempts,
        "average_score": avg_score,
        "quizzes": quiz_data,
        "attempts": attempt_data,
        "user": {
            "id": request.current_user.id,
            "user_code": request.current_user.user_code,
            "name": request.current_user.name,
            "email": request.current_user.email,
            "role": request.current_user.role
        }
    }, status=status.HTTP_200_OK)


# ============================================================
# CREATE QUIZ
# ============================================================

@csrf_exempt
@staff_required
def create_quiz(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "Only POST method is allowed."

        }, status=405)

    title = request.POST.get(
        "title",
        ""
    ).strip()

    topics = request.POST.get(
        "topics",
        ""
    ).strip()

    difficulty = request.POST.get(
        "difficulty",
        ""
    ).strip().lower()

    question_count = request.POST.get(
        "question_count",
        ""
    )

    reference_file = request.FILES.get(
        "reference_file"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not title:

        return JsonResponse({

            "success": False,

            "message":
                "Quiz title is required."

        }, status=400)

    if not topics:

        return JsonResponse({

            "success": False,

            "message":
                "Topics are required."

        }, status=400)

    if difficulty not in [
        "easy",
        "medium",
        "hard"
    ]:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid difficulty."

        }, status=400)

    try:

        question_count = int(
            question_count
        )

    except (TypeError, ValueError):

        return JsonResponse({

            "success": False,

            "message":
                "Invalid question count."

        }, status=400)

    if question_count <= 0:

        return JsonResponse({

            "success": False,

            "message":
                "Question count must be greater than zero."

        }, status=400)

    # --------------------------------------------------------
    # GENERATION MODE
    # --------------------------------------------------------

    if reference_file:

        generation_mode = "material"

    else:

        generation_mode = "ai"

    # --------------------------------------------------------
    # CREATE QUIZ
    # --------------------------------------------------------

    quiz = Quiz.objects.create(

        title=title,

        topics=topics,

        difficulty=difficulty,

        question_count=question_count,

        generation_mode=generation_mode,

        reference_file=reference_file,

        created_by=request.current_user
    )

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    if reference_file:

        return JsonResponse({

            "success": True,

            "generation_mode": "material",

            "message":
                "Quiz created. Material generation required.",

            "quiz_id":
                quiz.id,

            "next_endpoint":
                f"/api/staff/quizzes/{quiz.id}/generate-material/"
        }, status=201)

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    return JsonResponse({

        "success": True,

        "generation_mode": "ai",

        "message":
            "Quiz created. AI specification generated.",

        "quiz_id":
            quiz.id,

        "next_endpoint":
            f"/api/staff/quizzes/{quiz.id}/ai-specification/"
    }, status=201)


# ============================================================
# GENERATE QUIZ FROM MATERIAL
# ============================================================
@csrf_exempt
@staff_required
def generate_material_quiz(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    if not quiz.reference_file:

        return JsonResponse({

            "success": False,

            "message":
                "No reference material found."

        }, status=400)

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    try:

        material = extract_pdf_text(
            quiz.reference_file
        )

    except Exception as error:

        return JsonResponse({

            "success": False,

            "message":
                "Unable to read the uploaded PDF.",

            "error":
                str(error)

        }, status=400)

    if not material.strip():

        return JsonResponse({

            "success": False,

            "message":
                "PDF contains no readable text."

        }, status=400)

    quiz.extracted_text = material[:50000]

    quiz.save()

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    questions = generate_questions(

        material=material,

        topic=quiz.topics,

        difficulty=quiz.difficulty,

        question_count=quiz.question_count
    )

    if not questions:

        return JsonResponse({

            "success": False,

            "message":
                "Could not generate questions from material."

        }, status=400)

    # --------------------------------------------------------
    # SAVE QUESTIONS
    # --------------------------------------------------------

    quiz.questions.all().delete()

    save_generated_questions(
        quiz,
        questions
    )

    return JsonResponse({

        "success": True,

        "message":
            "Quiz generated successfully from material.",

        "quiz_id":
            quiz.id,

        "question_count":
            quiz.questions.count(),

        "next_endpoint":
            f"/api/staff/quizzes/{quiz.id}/preview/"
    })


# ============================================================
# AI SPECIFICATION
# ============================================================
@csrf_exempt
@staff_required
def generate_ai_specification(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    topics = [

        topic.strip()

        for topic in quiz.topics.split(",")

        if topic.strip()
    ]

    specification = {

        "task": "generate_quiz",

        "version": "1.0",

        "instruction": (
            "Generate a multiple-choice quiz "
            "based on the requested topics."
        ),

        "quiz": {

            "title":
                quiz.title,

            "topics":
                topics,

            "difficulty":
                quiz.difficulty,

            "question_count":
                quiz.question_count,

            "question_type":
                "mcq"
        },

        "requirements": {

            "four_options_per_question":
                True,

            "one_correct_answer":
                True,

            "include_explanation":
                True,

            "avoid_duplicate_questions":
                True,

            "follow_difficulty":
                True
        },

        "output_format": {

            "strict_json":
                True,

            "schema": {

                "quiz": {

                    "title":
                        "string",

                    "difficulty":
                        "easy | medium | hard",

                    "questions": [

                        {

                            "question":
                                "string",

                            "options": [

                                "string",

                                "string",

                                "string",

                                "string"
                            ],

                            "correct_answer":
                                "string",

                            "explanation":
                                "string"
                        }
                    ]
                }
            }
        }
    }

    quiz.ai_specification = specification

    quiz.save()

    return JsonResponse({

        "success": True,

        "quiz_id":
            quiz.id,

        "generation_mode":
            "ai",

        "specification":
            specification,

        "message":
            "Copy this JSON into an external AI model."
    })


# ============================================================
# IMPORT AI JSON
# ============================================================

@csrf_exempt
@staff_required
def import_ai_quiz(
    request,
    quiz_id
):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "Only POST method is allowed."

        }, status=405)

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    try:

        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid JSON."

        }, status=400)

    error = validate_quiz_json(
        data
    )

    if error:

        return JsonResponse({

            "success": False,

            "message":
                error

        }, status=400)

    # --------------------------------------------------------
    # CREATE QUESTIONS
    # --------------------------------------------------------

    create_questions_from_ai(
        quiz,
        data
    )

    return JsonResponse({

        "success": True,

        "message":
            "AI quiz imported successfully.",

        "quiz_id":
            quiz.id,

        "question_count":
            quiz.questions.count(),

        "next_endpoint":
            f"/api/staff/quizzes/{quiz.id}/preview/"
    })


# ============================================================
# QUIZ PREVIEW
# ============================================================
@csrf_exempt
@staff_required
def quiz_preview(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    questions = quiz.questions.all().order_by(
        "order"
    )

    question_data = []

    for question in questions:

        question_data.append({

            "id":
                question.id,

            "order":
                question.order,

            "question":
                question.question_text,

            "options": [

                question.option_a,

                question.option_b,

                question.option_c,

                question.option_d
            ],

            "correct_answer":
                question.correct_answer,

            "explanation":
                question.explanation
        })

    return JsonResponse({

        "success": True,

        "quiz": {

            "id":
                quiz.id,

            "title":
                quiz.title,

            "topics":
                quiz.topics,

            "difficulty":
                quiz.difficulty,

            "generation_mode":
                quiz.generation_mode,

            "question_count":
                len(question_data),

            "status":
                quiz.status,

            "quiz_code":
                quiz.quiz_code
        },

        "questions":
            question_data
    })


# ============================================================
# ACTIVATE QUIZ
# ============================================================

@csrf_exempt
@staff_required
def activate_quiz(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    if not quiz.questions.exists():

        return JsonResponse({

            "success": False,

            "message":
                "Cannot activate an empty quiz."

        }, status=400)

    quiz.quiz_code = generate_quiz_code()

    quiz.status = "active"

    quiz.save()

    return JsonResponse({

        "success": True,

        "message":
            "Quiz activated successfully.",

        "quiz_id":
            quiz.id,

        "quiz_code":
            quiz.quiz_code,

        "status":
            quiz.status
    })


# ============================================================
# CLOSE QUIZ
# ============================================================

@csrf_exempt
@staff_required
def close_quiz(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    quiz.status = "closed"

    quiz.save()

    return JsonResponse({

        "success": True,

        "message":
            "Quiz closed successfully."
    })


# ============================================================
# JOIN QUIZ
# ============================================================
@csrf_exempt
@student_required
def join_quiz(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "Only POST method is allowed."

        }, status=405)

    try:

        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid JSON."

        }, status=400)

    code = data.get(
        "quiz_code",
        ""
    ).strip().upper()

    quiz = Quiz.objects.filter(

        quiz_code=code,

        status="active"

    ).first()

    if not quiz:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid or inactive quiz code."

        }, status=404)

    return JsonResponse({

        "success": True,

        "message":
            "Quiz found.",

        "quiz": {

            "id":
                quiz.id,

            "title":
                quiz.title,

            "topics":
                quiz.topics,

            "difficulty":
                quiz.difficulty,

            "question_count":
                quiz.question_count,

            "quiz_code":
                quiz.quiz_code
        }
    })


# ============================================================
# GET QUIZ FOR STUDENT
# ============================================================
@csrf_exempt
@student_required
def take_quiz(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        status="active"
    )

    questions = quiz.questions.all().order_by(
        "order"
    )

    question_data = []

    for question in questions:

        question_data.append({

            "id":
                question.id,

            "order":
                question.order,

            "question":
                question.question_text,

            "options": [

                question.option_a,

                question.option_b,

                question.option_c,

                question.option_d
            ]
        })

    return JsonResponse({

        "success": True,

        "quiz": {

            "id":
                quiz.id,

            "title":
                quiz.title,

            "difficulty":
                quiz.difficulty,

            "question_count":
                len(question_data)
        },

        "questions":
            question_data
    })


# ============================================================
# SUBMIT QUIZ
# ============================================================

@csrf_exempt
@student_required
def submit_quiz(
    request,
    quiz_id
):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "Only POST method is allowed."

        }, status=405)

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        status="active"
    )

    try:

        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid JSON."

        }, status=400)

    submitted_answers = data.get(
        "answers",
        {}
    )

    questions = quiz.questions.all()

    score = 0

    answers = {}

    wrong_answers = []

    for question in questions:

        question_id = str(
            question.id
        )

        selected_answer = submitted_answers.get(
            question_id
        )

        answers[
            question_id
        ] = selected_answer

        if selected_answer == question.correct_answer:

            score += 1

        else:

            wrong_answers.append({

                "question_id":
                    question.id,

                "question":
                    question.question_text,

                "your_answer":
                    selected_answer,

                "correct_answer":
                    question.correct_answer,

                "explanation":
                    question.explanation
            })

    attempt = Attempt.objects.create(

        quiz=quiz,

        student=request.current_user,

        answers=answers,

        score=score,

        total_questions=questions.count()
    )

    percentage = 0

    if questions.count():

        percentage = round(

            (
                score
                / questions.count()
            ) * 100,

            2
        )

    return JsonResponse({

        "success": True,

        "message":
            "Quiz submitted successfully.",

        "attempt_id":
            attempt.id,

        "score":
            score,

        "total_questions":
            questions.count(),

        "percentage":
            percentage,

        "wrong_answers":
            wrong_answers
    })


# ============================================================
# STUDENT RESULT
# ============================================================
@csrf_exempt
@student_required
def result(
    request,
    attempt_id
):

    attempt = get_object_or_404(

        Attempt,

        id=attempt_id,

        student=request.current_user
    )

    percentage = 0

    if attempt.total_questions:

        percentage = round(

            (
                attempt.score
                / attempt.total_questions
            ) * 100,

            2
        )

    wrong_answers = []

    questions = attempt.quiz.questions.all()

    for question in questions:

        student_answer = attempt.answers.get(
            str(question.id)
        )

        if student_answer != question.correct_answer:

            wrong_answers.append({

                "question_id":
                    question.id,

                "question":
                    question.question_text,

                "your_answer":
                    student_answer,

                "correct_answer":
                    question.correct_answer,

                "explanation":
                    question.explanation
            })

    return JsonResponse({

        "success": True,

        "attempt": {

            "id":
                attempt.id,

            "quiz_id":
                attempt.quiz.id,

            "quiz_title":
                attempt.quiz.title,

            "score":
                attempt.score,

            "total_questions":
                attempt.total_questions,

            "percentage":
                percentage,

            "submitted_at":
                attempt.submitted_at
        },

        "wrong_answers":
            wrong_answers
    })


# ============================================================
# STAFF RESULTS
# ============================================================
@csrf_exempt
@staff_required
def quiz_results(
    request,
    quiz_id
):

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        created_by=request.current_user
    )

    attempts = quiz.attempts.select_related(
        "student"
    ).order_by(
        "-submitted_at"
    )

    result_data = []

    for attempt in attempts:

        percentage = 0

        if attempt.total_questions:

            percentage = round(

                (
                    attempt.score
                    / attempt.total_questions
                ) * 100,

                2
            )

        result_data.append({

            "attempt_id":
                attempt.id,

            "student": {

                "user_code":
                    attempt.student.user_code,

                "name":
                    attempt.student.name,

                "email":
                    attempt.student.email
            },

            "score":
                attempt.score,

            "total_questions":
                attempt.total_questions,

            "percentage":
                percentage,

            "submitted_at":
                attempt.submitted_at
        })

    return JsonResponse({

        "success": True,

        "quiz": {

            "id":
                quiz.id,

            "title":
                quiz.title,

            "quiz_code":
                quiz.quiz_code
        },

        "results":
            result_data
    })


# ============================================================
# HELPER: SAVE GENERATED QUESTIONS
# ============================================================
@csrf_exempt
def save_generated_questions(
    quiz,
    questions
):

    for index, question in enumerate(
        questions,
        start=1
    ):

        options = question[
            "options"
        ]

        Question.objects.create(

            quiz=quiz,

            question_text=question[
                "question"
            ],

            option_a=options[0],

            option_b=options[1],

            option_c=options[2],

            option_d=options[3],

            correct_answer=question[
                "correct_answer"
            ],

            explanation=question.get(
                "explanation",
                ""
            ),

            order=index
        )


# ============================================================
# HELPER: CREATE QUESTIONS FROM AI
# ============================================================
@csrf_exempt
def create_questions_from_ai(
    quiz,
    data
):

    quiz_data = data["quiz"]

    quiz.questions.all().delete()

    if quiz_data.get("title"):

        quiz.title = quiz_data[
            "title"
        ]

    quiz.save()

    save_generated_questions(

        quiz,

        quiz_data[
            "questions"
        ]
    )