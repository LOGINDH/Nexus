from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # SYSTEM
    # ========================================================



    path("me/",views.current_user,name="current_user"),

    path("logout/",views.logout_view,name="logout"),


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path("student/register/",views.student_register,name="student_register"),

    path("student/login/",views.student_login,name="student_login"),

    path("staff/login/",views.staff_login,name="staff_login"),


    # ========================================================
    # STUDENT
    # ========================================================

    path("student/dashboard/",views.student_dashboard,name="student_dashboard"),

    path("student/join/",views.join_quiz,name="join_quiz"),

    path("student/quizzes/<int:quiz_id>/",views.take_quiz,name="take_quiz"),

    path("student/quizzes/<int:quiz_id>/submit/",views.submit_quiz,name="submit_quiz"),

    path("student/attempts/<int:attempt_id>/",views.result,name="result"),


    # ========================================================
    # STAFF
    # ========================================================

    path("staff/dashboard/",views.staff_dashboard,name="staff_dashboard"),

    path("staff/quizzes/create/",views.create_quiz,name="create_quiz"),

    # --------------------------------------------------------
    # MATERIAL GENERATION
    # --------------------------------------------------------

    path("staff/quizzes/<int:quiz_id>/generate-material/",views.generate_material_quiz,name="generate_material_quiz"),

    # --------------------------------------------------------
    # AI FALLBACK
    # --------------------------------------------------------

    path("staff/quizzes/<int:quiz_id>/ai-specification/",views.generate_ai_specification,name="generate_ai_specification"),

    path("staff/quizzes/<int:quiz_id>/import-ai/",views.import_ai_quiz,name="import_ai_quiz"),

    # --------------------------------------------------------
    # QUIZ MANAGEMENT
    # --------------------------------------------------------

    path("staff/quizzes/<int:quiz_id>/preview/",views.quiz_preview,name="quiz_preview"),

    path("staff/quizzes/<int:quiz_id>/activate/",views.activate_quiz,name="activate_quiz"),

    path("staff/quizzes/<int:quiz_id>/close/",views.close_quiz,name="close_quiz"),

    path("staff/quizzes/<int:quiz_id>/results/",views.quiz_results,name="quiz_results"),]