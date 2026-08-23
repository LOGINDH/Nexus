import random
import string

import fitz


# ============================================================
# USER CODE
# ============================================================

def generate_user_code(role):

    prefix = "STU" if role == "student" else "STF"

    while True:

        random_part = "".join(
            random.choices(
                string.ascii_uppercase
                + string.digits,
                k=6
            )
        )

        code = f"{prefix}-{random_part}"

        from .models import User

        if not User.objects.filter(
            user_code=code
        ).exists():

            return code


# ============================================================
# QUIZ CODE
# ============================================================

def generate_quiz_code():

    from .models import Quiz

    while True:

        code = "".join(
            random.choices(
                string.ascii_uppercase
                + string.digits,
                k=6
            )
        )

        if not Quiz.objects.filter(
            quiz_code=code
        ).exists():

            return code


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    uploaded_file.seek(0)

    document = fitz.open(
        stream=uploaded_file.read(),
        filetype="pdf"
    )

    pages = []

    for page in document:

        page_text = page.get_text()

        if page_text.strip():

            pages.append(
                page_text
            )

    document.close()

    return "\n".join(pages)