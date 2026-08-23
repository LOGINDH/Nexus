from functools import wraps
from django.http import JsonResponse
from .models import User


# ============================================================
# STUDENT REQUIRED
# ============================================================

def student_required(view):

    @wraps(view)
    def wrapper(request, *args, **kwargs):

        user_id = request.session.get("user_id")
        role = request.session.get("role")

        if not user_id or role != "student":
            return JsonResponse({
                "success": False,
                "message": "Authentication required. Please log in as student."
            }, status=401)

        try:
            user = User.objects.get(
                id=user_id,
                role="student",
                is_active=True
            )
        except User.DoesNotExist:
            request.session.flush()
            return JsonResponse({
                "success": False,
                "message": "Student account not found or inactive."
            }, status=401)

        request.current_user = user

        return view(request, *args, **kwargs)

    return wrapper


# ============================================================
# STAFF REQUIRED
# ============================================================

def staff_required(view):

    @wraps(view)
    def wrapper(request, *args, **kwargs):

        user_id = request.session.get("user_id")
        role = request.session.get("role")

        if not user_id or role != "staff":
            return JsonResponse({
                "success": False,
                "message": "Authentication required. Please log in as faculty/staff."
            }, status=401)

        try:
            user = User.objects.get(
                id=user_id,
                role="staff",
                is_active=True
            )
        except User.DoesNotExist:
            request.session.flush()
            return JsonResponse({
                "success": False,
                "message": "Staff account not found or inactive."
            }, status=401)

        request.current_user = user

        return view(request, *args, **kwargs)

    return wrapper