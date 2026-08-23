import random
import re


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SPLIT INTO SENTENCES
# ============================================================

def get_sentences(text):

    text = clean_text(text)

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    valid_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 40:
            continue

        if len(sentence) > 400:
            continue

        valid_sentences.append(
            sentence
        )

    return valid_sentences


# ============================================================
# FIND DEFINITIONS
# ============================================================

def extract_definitions(sentences):

    definitions = []

    patterns = [

        r"^(.{2,80}?)\s+is\s+(.+)$",

        r"^(.{2,80}?)\s+are\s+(.+)$",

        r"^(.{2,80}?)\s+refers to\s+(.+)$",

        r"^(.{2,80}?)\s+means\s+(.+)$",

        r"^(.{2,80}?)\s+is defined as\s+(.+)$",

    ]

    for sentence in sentences:

        for pattern in patterns:

            match = re.match(
                pattern,
                sentence,
                flags=re.IGNORECASE
            )

            if not match:
                continue

            term = match.group(1).strip()

            definition = match.group(2).strip()

            if not term:
                continue

            if len(term.split()) > 10:
                continue

            definitions.append(
                {
                    "term": term,
                    "definition": definition,
                    "source": sentence
                }
            )

            break

    return definitions


# ============================================================
# EXTRACT IMPORTANT PHRASES
# ============================================================

def extract_candidate_terms(
    sentences
):

    terms = []

    for sentence in sentences:

        words = re.findall(
            r"\b[A-Z][A-Za-z0-9-]{2,}\b",
            sentence
        )

        for word in words:

            if word not in terms:

                terms.append(
                    word
                )

    return terms


# ============================================================
# CREATE OPTIONS
# ============================================================

def create_options(
    correct_answer,
    candidates
):

    candidates = [

        item

        for item in candidates

        if item.lower()
        != correct_answer.lower()

    ]

    random.shuffle(
        candidates
    )

    distractors = candidates[:3]

    if len(distractors) < 3:

        return None

    options = [

        correct_answer,

        distractors[0],

        distractors[1],

        distractors[2]
    ]

    random.shuffle(
        options
    )

    return options


# ============================================================
# DEFINITION QUESTIONS
# ============================================================

def generate_definition_questions(
    definitions,
    candidates,
    question_count
):

    questions = []

    random.shuffle(
        definitions
    )

    for item in definitions:

        if len(questions) >= question_count:
            break

        term = item["term"]

        options = create_options(
            term,
            candidates
        )

        if not options:
            continue

        question = {

            "question": (
                "Which concept is described "
                "by the following statement?\n\n"
                f"{item['source']}"
            ),

            "options": options,

            "correct_answer": term,

            "explanation": item["source"]
        }

        questions.append(
            question
        )

    return questions


# ============================================================
# FALLBACK SENTENCE QUESTIONS
# ============================================================

def generate_sentence_questions(
    sentences,
    question_count
):

    questions = []

    if len(sentences) < 4:
        return questions

    shuffled = sentences.copy()

    random.shuffle(
        shuffled
    )

    for index, correct_sentence in enumerate(
        shuffled
    ):

        if len(questions) >= question_count:
            break

        remaining = [

            sentence

            for sentence in sentences

            if sentence != correct_sentence
        ]

        random.shuffle(
            remaining
        )

        distractors = remaining[:3]

        if len(distractors) < 3:
            continue

        options = [

            correct_sentence,

            distractors[0],

            distractors[1],

            distractors[2]
        ]

        random.shuffle(
            options
        )

        question = {

            "question": (
                "Which statement is directly "
                "supported by the provided material?"
            ),

            "options": options,

            "correct_answer": correct_sentence,

            "explanation": (
                "This statement was extracted "
                "directly from the reference material."
            )
        }

        questions.append(
            question
        )

    return questions


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_questions(
    material,
    topic,
    difficulty,
    question_count
):

    sentences = get_sentences(
        material
    )

    if len(sentences) < 4:

        return []

    definitions = extract_definitions(
        sentences
    )

    candidates = extract_candidate_terms(
        sentences
    )

    questions = generate_definition_questions(
        definitions,
        candidates,
        question_count
    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if len(questions) < question_count:

        remaining_count = (
            question_count
            - len(questions)
        )

        fallback_questions = generate_sentence_questions(
            sentences,
            remaining_count
        )

        questions.extend(
            fallback_questions
        )

    return questions[:question_count]