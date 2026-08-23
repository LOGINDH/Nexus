def validate_quiz_json(data):

    if not isinstance(data, dict):

        return "JSON root must be an object."

    if "quiz" not in data:

        return "Missing 'quiz' field."

    quiz = data["quiz"]

    if not isinstance(
        quiz,
        dict
    ):

        return "'quiz' must be an object."

    if "questions" not in quiz:

        return "Missing 'questions' field."

    questions = quiz["questions"]

    if not isinstance(
        questions,
        list
    ):

        return "'questions' must be an array."

    if len(questions) == 0:

        return "No questions found."

    for index, question in enumerate(
        questions,
        start=1
    ):

        if not isinstance(
            question,
            dict
        ):

            return (
                f"Question {index} "
                "must be an object."
            )

        required_fields = [

            "question",

            "options",

            "correct_answer"
        ]

        for field in required_fields:

            if field not in question:

                return (
                    f"Question {index} "
                    f"missing '{field}'."
                )

        options = question[
            "options"
        ]

        if not isinstance(
            options,
            list
        ):

            return (
                f"Question {index} "
                "options must be an array."
            )

        if len(options) != 4:

            return (
                f"Question {index} "
                "must contain exactly 4 options."
            )

        correct_answer = question[
            "correct_answer"
        ]

        if correct_answer not in options:

            return (
                f"Question {index} "
                "has an invalid correct answer."
            )

    return None