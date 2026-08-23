from functools import wraps

from django.shortcuts import redirect

from .models import User


# ============================================================
# STUDENT REQUIRED
# ============================================================

def student_required(view):

    @wraps(view)
    def wrapper(
        request,
        *args,
        **kwargs
    ):

        user_id = request.session.get(
            "user_id"
        )

        role = request.session.get(
            "role"
        )

        if not user_id or role != "student":

            return redirect(
                "student_login"
            )

        try:

            user = User.objects.get(
                id=user_id,
                role="student",
                is_active=True
            )

        except User.DoesNotExist:

            request.session.flush()

            return redirect(
                "student_login"
            )

        request.current_user = user

        return view(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# STAFF REQUIRED
# ============================================================

def staff_required(view):

    @wraps(view)
    def wrapper(
        request,
        *args,
        **kwargs
    ):

        user_id = request.session.get(
            "user_id"
        )

        role = request.session.get(
            "role"
        )

        if not user_id or role != "staff":

            return redirect(
                "staff_login"
            )

        try:

            user = User.objects.get(
                id=user_id,
                role="staff",
                is_active=True
            )

        except User.DoesNotExist:

            request.session.flush()

            return redirect(
                "staff_login"
            )

        request.current_user = user

        return view(
            request,
            *args,
            **kwargs
        )

    return wrapper