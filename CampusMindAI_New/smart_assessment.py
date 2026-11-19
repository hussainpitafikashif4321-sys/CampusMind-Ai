import json
import re
import difflib
import requests
import streamlit as st

from progress_database import create_progress_tables, get_connection


# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"

TOTAL_QUESTIONS = 10
MAX_ATTEMPTS = 8


# =========================================================
# FIVE SUBJECTS
# =========================================================

SUBJECT_TOPICS = {
    "Python Programming": [
        "Variables and Data Types", "Operators",
        "Conditional Statements", "Loops", "Functions",
        "Lists and Tuples", "Dictionaries and Sets",
        "Strings", "Object Oriented Programming",
        "Exception and File Handling"
    ],

    "Java": [
        "Variables and Data Types", "Operators",
        "Conditional Statements", "Loops", "Methods",
        "Arrays", "Classes and Objects", "Inheritance",
        "Exception Handling", "Collections"
    ],

    "Computer Networks": [
        "Network Fundamentals", "Network Types",
        "OSI Model", "TCP/IP Model", "IP Addressing",
        "Network Devices", "Network Protocols",
        "Routing", "Switching", "Network Security"
    ],

    "IT": [
        "Computer Fundamentals", "Operating Systems",
        "Computer Hardware and Software", "MS Office and Productivity Tools",
        "Internet and Web Technologies", "Database Fundamentals",
        "Cybersecurity Basics", "Cloud Computing",
        "Information Systems", "IT Ethics and Digital Citizenship"
    ],

    "Data Science": [
        "Data Science Fundamentals", "Data Collection",
        "Data Cleaning", "Data Analysis", "Statistics",
        "Probability", "Python for Data Science",
        "Pandas", "Data Visualization", "Machine Learning"
    ]
}


# =========================================================
# QUESTION OBJECTIVES
# =========================================================

def get_question_objectives(subject, topic):

    text = topic.lower().strip()

    # Data Science: Data Types and Data Analysis
    if subject == "Data Science" and (
        "data type" in text or "data analysis" in text
    ):
        return [
            "Meaning and purpose of data types in data science",
            "Difference between numerical and categorical data",
            "Difference between discrete and continuous data",
            "Meaning and examples of nominal data",
            "Meaning and examples of ordinal data",
            "Meaning and examples of structured data",
            "Meaning and examples of unstructured data",
            "Role of date and time data in analysis",
            "Handling missing values during data analysis",
            "Choosing an appropriate data type for a dataset"
        ]

    # Data Science: Data Collection
    if subject == "Data Science" and "collection" in text:
        return [
            "Purpose of data collection",
            "Primary data sources",
            "Secondary data sources",
            "Surveys as a data collection method",
            "Sensors as data sources",
            "Web data collection",
            "Structured data collection",
            "Data collection accuracy",
            "Data collection bias",
            "Ethical data collection"
        ]

    # Data Science: Data Cleaning
    if subject == "Data Science" and "clean" in text:
        return [
            "Purpose of data cleaning",
            "Identifying missing values",
            "Handling missing values",
            "Identifying duplicate records",
            "Removing duplicate records",
            "Handling inconsistent data",
            "Detecting incorrect values",
            "Handling outliers",
            "Data formatting",
            "Importance of clean data"
        ]

    # Data Science: Data Analysis
    if subject == "Data Science" and "analysis" in text:
        return [
            "Purpose of data analysis",
            "Exploratory data analysis",
            "Finding patterns in data",
            "Calculating averages",
            "Finding the median",
            "Understanding data distribution",
            "Comparing datasets",
            "Identifying trends",
            "Using summaries for analysis",
            "Interpreting analysis results"
        ]

    # Data Science: Statistics
    if subject == "Data Science" and "statistic" in text:
        return [
            "Purpose of statistics in data science",
            "Meaning of mean",
            "Meaning of median",
            "Meaning of mode",
            "Understanding range",
            "Understanding variance",
            "Understanding standard deviation",
            "Population and sample",
            "Descriptive statistics",
            "Interpreting statistical results"
        ]

    # Data Science: Pandas
    if subject == "Data Science" and "pandas" in text:
        return [
            "Purpose of Pandas",
            "Meaning of a Series",
            "Meaning of a DataFrame",
            "Reading a CSV file",
            "Viewing the first rows",
            "Checking dataset information",
            "Selecting a column",
            "Filtering rows",
            "Handling missing values",
            "Saving a DataFrame"
        ]

    # Data Science: Data Visualization
    if subject == "Data Science" and "visual" in text:
        return [
            "Purpose of data visualization",
            "Use of bar charts",
            "Use of line charts",
            "Use of pie charts",
            "Use of histograms",
            "Choosing a suitable chart",
            "Understanding chart axes",
            "Visualizing trends",
            "Comparing categories visually",
            "Avoiding misleading charts"
        ]

    # Data Science: Machine Learning
    if subject == "Data Science" and "machine learning" in text:
        return [
            "Meaning of machine learning",
            "Supervised learning",
            "Unsupervised learning",
            "Classification problems",
            "Regression problems",
            "Training data",
            "Testing data",
            "Features and labels",
            "Model prediction",
            "Model evaluation"
        ]

    # General Data Science
    if subject == "Data Science":
        return [
            "Meaning of data science",
            "Role of data collection",
            "Purpose of data cleaning",
            "Purpose of data analysis",
            "Role of statistics",
            "Role of probability",
            "Use of Python in data science",
            "Purpose of data visualization",
            "Meaning of machine learning",
            "Practical application of data science"
        ]

    # Programming variables and data types
    if "variable" in text or "data type" in text:

        return [
            "Meaning of a variable",
            "Variable declaration",
            "Variable initialization",
            "Integer data type",
            "Floating-point data type",
            "String data type",
            "Boolean data type",
            "Type conversion",
            "Valid variable naming",
            "Choosing suitable data types"
        ]

    if "loop" in text and "array" in text:

        return [
            "Purpose of programming loops",
            "Difference between for and while loops",
            "Loop termination conditions",
            "Use of break statement",
            "Use of continue statement",
            "Valid array declaration syntax",
            "Accessing array elements",
            "Array initialization",
            "Traversing arrays using loops",
            "Using array length during traversal"
        ]

    if "loop" in text:

        return [
            "Purpose of loops",
            "Difference between for and while loops",
            "Loop termination conditions",
            "Number of loop iterations",
            "Break statement",
            "Continue statement",
            "Nested loops",
            "Infinite loops",
            "Output of a simple loop",
            "Practical applications of loops"
        ]

    if "array" in text:

        return [
            "Purpose of arrays",
            "Array declaration syntax",
            "Array initialization",
            "Array indexing",
            "Accessing a specific element",
            "Updating an array element",
            "Array length",
            "Array traversal",
            "Using loops with arrays",
            "Common array mistakes"
        ]

    if "function" in text or "method" in text:

        return [
            "Purpose of functions or methods",
            "Function declaration syntax",
            "Function parameters",
            "Function arguments",
            "Return values",
            "Calling a function",
            "Variable scope",
            "Local variables",
            "Function overloading",
            "Practical use of functions"
        ]

    if subject == "Java" and "inheritance" in text:

        return [
            "Meaning of inheritance",
            "Purpose of inheritance",
            "Parent class",
            "Child class",
            "extends keyword",
            "Method overriding",
            "Single inheritance",
            "Multilevel inheritance",
            "Hierarchical inheritance",
            "Benefits of inheritance"
        ]

    if subject == "Computer Networks":

        return [
            "Meaning of computer networks",
            "Purpose of computer networks",
            "LAN networks",
            "WAN networks",
            "MAN networks",
            "Network communication",
            "Client and server",
            "Network topology",
            "Network advantages",
            "Practical network applications"
        ]

    # IT: Computer Fundamentals
    if subject == "IT" and (
        "computer fundamental" in text or "computer basics" in text
    ):
        return [
            "Meaning and purpose of a computer",
            "Difference between hardware and software",
            "Main function of the CPU",
            "Role of RAM",
            "Difference between RAM and storage",
            "Examples of input devices",
            "Examples of output devices",
            "Purpose of an operating system",
            "Meaning of files and folders",
            "Uses of computers in daily life"
        ]

    # General IT topic objectives
    if subject == "IT":
        return [
            f"Basic meaning of {topic}",
            f"Purpose and importance of {topic}",
            f"Main types of {topic}",
            f"Main components of {topic}",
            f"How {topic} works",
            f"Important terms related to {topic}",
            f"Practical application of {topic}",
            f"Correct example of {topic}",
            f"Common issue related to {topic}",
            f"Basic safety or best practice for {topic}"
        ]

    return [
        f"Basic definition of {topic}",
        f"Purpose of {topic}",
        f"Main types of {topic}",
        f"Main components of {topic}",
        f"Working principle of {topic}",
        f"Important rules of {topic}",
        f"Practical application of {topic}",
        f"Correct example of {topic}",
        f"Common mistake related to {topic}",
        f"Problem-solving using {topic}"
    ]


def get_question_focus(subject, topic, number):

    if topic.strip():

        objectives = get_question_objectives(
            subject, topic
        )

        return objectives[number - 1]

    return SUBJECT_TOPICS[subject][number - 1]


# =========================================================
# JSON PARSER
# =========================================================

def parse_json(text):

    text = str(text).strip()

    text = re.sub(
        r"^```(?:json)?\s*", "",
        text, flags=re.IGNORECASE
    )

    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}")

        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])

        raise ValueError("AI returned invalid JSON.")


# =========================================================
# OLLAMA REQUEST
# =========================================================

def ask_ollama(
    prompt,
    temperature=0.30,
    num_predict=450,
    timeout=150
):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are CampusMind AI, an accurate "
                        "university MCQ creator. Create clear, "
                        "factually correct educational questions. "
                        "Follow the requested JSON structure."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "format": "json",
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        },
        timeout=(10, timeout)
    )

    response.raise_for_status()

    content = response.json().get(
        "message", {}
    ).get("content", "")

    if not content.strip():
        raise ValueError("AI returned an empty response.")

    return parse_json(content)


# =========================================================
# ANSWER NORMALIZATION
# =========================================================

def normalize_correct_answer(answer, options):

    text = str(answer).strip()

    match = re.match(
        r"^(?:the\s+)?(?:correct\s+)?"
        r"(?:answer\s*[:=-]?\s*)?"
        r"(?:option\s*)?\(?([ABCD])\)?"
        r"(?:\s*[.):\-].*)?$",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    if text in ["1", "2", "3", "4"]:
        return "ABCD"[int(text) - 1]

    cleaned = " ".join(text.lower().split())

    for key, value in options.items():

        if cleaned == " ".join(
            str(value).lower().split()
        ):
            return key

    raise ValueError("AI returned an invalid correct answer.")


# =========================================================
# QUESTION VALIDATION
# =========================================================

def validate_question(data):

    if not isinstance(data, dict):
        raise ValueError("Invalid question format.")

    question = str(
        data.get("question", "")
    ).strip()

    options = data.get("options", {})

    explanation = str(
        data.get("explanation", "")
    ).strip()

    if not question:
        raise ValueError("Question text is missing.")

    if not isinstance(options, dict):
        raise ValueError("Question options are invalid.")

    options = {
        str(key).strip().upper(): str(value).strip()
        for key, value in options.items()
    }

    if set(options) != {"A", "B", "C", "D"}:
        raise ValueError("Exactly four options are required.")

    if not all(options.values()):
        raise ValueError("An option is empty.")

    option_values = [
        value.lower().strip()
        for value in options.values()
    ]

    if len(set(option_values)) != 4:
        raise ValueError("Duplicate answer options detected.")

    answer = normalize_correct_answer(
        data.get("correct_answer", ""),
        options
    )

    if not explanation or len(explanation) < 8:
        raise ValueError("Question explanation is missing.")

    if len(question) < 12:
        raise ValueError("Question is too short.")

    # Reject incomplete code-based questions.
    if re.search(
        r"(following code|following initialization|given code)",
        question,
        re.IGNORECASE
    ):
        if not re.search(
            r"```|`[^`]+`",
            question
        ):
            raise ValueError(
                "Question refers to missing code."
            )

    return {
        "question": question,
        "options": options,
        "correct_answer": answer,
        "explanation": explanation
    }


# =========================================================
# DUPLICATE CHECKING
# =========================================================

def normalize_question(text):

    text = str(text).lower()

    text = re.sub(
        r"```.*?```", " ",
        text, flags=re.DOTALL
    )

    text = re.sub(
        r"[^a-z0-9\s]", " ", text
    )

    return " ".join(text.split())


def is_duplicate(question, previous):

    current = normalize_question(question)

    for old in previous:

        existing = normalize_question(
            old["question"]
        )

        if current == existing:
            return True

        similarity = difflib.SequenceMatcher(
            None, current, existing
        ).ratio()

        # Reject only extremely similar question wording.
        if similarity >= 0.98:
            return True

    return False
# =========================================================
# GENERATE ONE QUESTION
# =========================================================

def generate_one_question(
    subject,
    level,
    topic,
    previous,
    number,
    attempt
):

    focus = get_question_focus(
        subject, topic, number
    )

    previous_text = "\n".join(
        f"{index}. {item['question']}"
        for index, item in enumerate(previous, 1)
    )

    previous_concepts = "\n".join(
        f"- {get_question_focus(subject, topic, i)}"
        for i in range(1, number)
    )

    if not previous_text:
        previous_text = "No previous questions."

    if not previous_concepts:
        previous_concepts = "No previous concepts."

    prompt = f"""
Create exactly ONE accurate university MCQ.

SUBJECT: {subject}
DIFFICULTY: {level}
SELECTED TOPIC: {topic if topic else "General subject coverage"}

QUESTION NUMBER: {number}

THIS QUESTION MUST TEST ONLY THIS CONCEPT:
{focus}

CONCEPTS ALREADY USED:
{previous_concepts}

PREVIOUS QUESTIONS:
{previous_text}

IMPORTANT RULES:

1. Stay strictly within the selected subject and topic.
2. Test the assigned concept, not an unrelated concept.
3. Do not repeat any previous question.
4. Do not ask about concepts already tested.
5. Use a different question structure and example.
6. Use simple English.
7. Provide exactly four options: A, B, C and D.
8. Exactly ONE option must be correct.
9. All incorrect options must be clearly incorrect.
10. Verify the correct answer before returning.
11. Explanation must agree with the correct answer.
12. Do not use ambiguous wording.
13. Do not invent technical rules.
14. Do not include incomplete code examples.
15. Do not create two options that are both correct.
16. Keep the question suitable for {level} students.
17. Avoid asking the same definition in different words.

For Data Science:
- Ask about data science concepts.
- Do not turn data types into programming variable questions.
- Distinguish numerical, categorical, discrete, continuous,
  nominal, ordinal, structured and unstructured data correctly.

For Java:
- Use valid Java syntax and Java language rules.
- Remember that array indexes start at zero.
- Do not provide multiple valid answers in a single-answer MCQ.

For IT:
- Ask about information technology and computer fundamentals.
- Use accurate basic IT terminology.
- Keep all options clearly distinct, with only one correct answer.
- Do not mix unrelated programming-language questions into IT.

For attempt {attempt}, use a different question approach
if an earlier attempt was rejected.

Return only valid JSON:

{{
    "question": "Question text",
    "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
    }},
    "correct_answer": "A",
    "explanation": "Accurate explanation."
}}
"""

    data = ask_ollama(
        prompt,
        temperature=min(0.30 + attempt * 0.06, 0.70),
        num_predict=450,
        timeout=150
    )

    return validate_question(data)


# =========================================================
# GENERATE TEN QUESTIONS
# =========================================================

def generate_questions(
    subject,
    level,
    topic,
    on_question
):

    questions = []

    for number in range(1, TOTAL_QUESTIONS + 1):

        selected = None
        last_error = None

        for attempt in range(1, MAX_ATTEMPTS + 1):

            try:

                candidate = generate_one_question(
                    subject,
                    level,
                    topic,
                    questions,
                    number,
                    attempt
                )

                if is_duplicate(
                    candidate["question"],
                    questions
                ):

                    last_error = (
                        "A very similar question was generated."
                    )
                    continue

                selected = candidate
                break

            except Exception as error:
                last_error = str(error)

        if selected is None:

            raise ValueError(
                f"Question {number} could not be generated "
                f"after {MAX_ATTEMPTS} attempts. "
                f"{last_error or 'Please try again.'}"
            )

        questions.append(selected)

        on_question(selected, number)

    return questions


# =========================================================
# AI LEARNING FEEDBACK
# =========================================================

def generate_feedback(
    subject,
    level,
    score,
    incorrect
):

    mistakes = "\n\n".join(
        f"Question: {item['question']}\n"
        f"Correct answer: {item['correct_answer']}\n"
        f"Student answer: {item['student_answer']}"
        for item in incorrect
    )

    prompt = f"""
Give short and honest academic feedback in easy English.

Subject: {subject}
Difficulty: {level}
Verified score: {score}/10

Incorrect answers:
{mistakes if mistakes else "All answers were correct."}

Rules:
- Identify weak areas using actual incorrect answers.
- Do not change the score.
- Give exactly three practical suggestions.
- Do not invent student information.

Use these headings:

### Weak Areas
### Learning Advice
### Practical Suggestions
"""

    try:

        result = ask_ollama(
            prompt,
            temperature=0.2,
            num_predict=450,
            timeout=120
        )

        if isinstance(result, dict):

            return (
                result.get("feedback")
                or result.get("message")
                or str(result)
            )

        return str(result)

    except Exception:

        return (
            f"Your score is {score}/10. "
            "Review incorrect answers and practice again."
        )


# =========================================================
# DATABASE SAVING
# =========================================================

def save_assessment_to_database(
    subject,
    level,
    topic,
    questions,
    answers,
    score
):

    student_id = st.session_state.get(
        "logged_in_user_id"
    )

    if student_id is None:
        raise ValueError(
            "Please log in before saving your assessment."
        )

    student_id = int(student_id)

    total = len(questions)

    percentage = score / total * 100 if total else 0

    create_progress_tables()

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            INSERT INTO assessment_attempts
            (
                student_id, subject, difficulty,
                selected_topic, score,
                total_questions, percentage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                subject,
                level,
                topic.strip() or None,
                score,
                total,
                percentage
            )
        )

        attempt_id = cursor.lastrowid

        rows = []

        subject_topics = SUBJECT_TOPICS.get(
            subject,
            SUBJECT_TOPICS["Python Programming"]
        )

        for index, question in enumerate(questions):

            student_answer = answers[index]
            correct_answer = question["correct_answer"]

            question_topic = (
                topic.strip()
                if topic.strip()
                else subject_topics[index]
            )

            rows.append((
                attempt_id,
                index + 1,
                question_topic,
                question["question"],
                (
                    f"{student_answer}. "
                    f"{question['options'][student_answer]}"
                ),
                (
                    f"{correct_answer}. "
                    f"{question['options'][correct_answer]}"
                ),
                int(student_answer == correct_answer),
                question["explanation"]
            ))

        conn.executemany(
            """
            INSERT INTO assessment_question_results
            (
                attempt_id, question_number, topic,
                question_text, student_answer,
                correct_answer, is_correct, explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows
        )

        conn.commit()

        return attempt_id

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()

        # =========================================================
# MAIN STREAMLIT INTERFACE
# =========================================================

def render():

    st.markdown("""
    <style>
    .assessment-header {
        background: linear-gradient(120deg, #2563eb, #7c3aed);
        padding: 28px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
    }

    .assessment-header h1 {
        color: white;
    }

    .assessment-card {
        background: linear-gradient(135deg, #1e293b, #312e81);
        padding: 20px;
        border-radius: 15px;
        color: white;
    }

    .score-card {
        background: linear-gradient(120deg, #2563eb, #7c3aed);
        padding: 25px;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }

    .score-card h1 {
        color: white;
        font-size: 42px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="assessment-header">
        <h1>🧠 Smart Skill Assessment</h1>
        <p>
            Test your knowledge and improve your academic skills
            with CampusMind AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    defaults = {
        "assessment_questions": [],
        "assessment_submitted": False,
        "assessment_answers": {},
        "assessment_result": None,
        "assessment_version": 0,
        "assessment_saved": False,
        "assessment_save_error": None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.subheader("Assessment Settings")

    subjects = list(SUBJECT_TOPICS.keys())

    col1, col2 = st.columns(2)

    with col1:

        subject = st.selectbox(
            "Select Subject",
            subjects
        )

        difficulty = st.selectbox(
            "Select Difficulty",
            ["Beginner", "Intermediate", "Advanced"]
        )

    with col2:

        topic = st.text_input(
            "Specific Topic (Optional)",
            placeholder="Example: Data Types and Data Analysis"
        )

        st.info("Your assessment will contain 10 MCQs.")

    # Generate assessment

    if st.button(
        "Generate Assessment",
        type="primary",
        use_container_width=True
    ):

        st.session_state.assessment_questions = []
        st.session_state.assessment_answers = {}
        st.session_state.assessment_submitted = False
        st.session_state.assessment_result = None
        st.session_state.assessment_saved = False
        st.session_state.assessment_save_error = None
        st.session_state.assessment_version += 1

        st.session_state.pop(
            "assessment_feedback", None
        )

        st.subheader("Generating Your Assessment")

        percentage_box = st.empty()
        progress = st.progress(0)
        current = st.empty()
        preview = st.empty()

        generated_preview = []

        def show_question(question, count):

            generated_preview.append(question)

            percentage_box.markdown(
                f"## {count * 10}% completed · {count}/10 MCQs"
            )

            progress.progress(count * 10)

            current.success(
                f"Question {count} generated!"
            )

            with preview.container():

                for number, item in enumerate(
                    generated_preview, 1
                ):

                    st.markdown(f"### Question {number}")
                    st.write(item["question"])

                    for option in ["A", "B", "C", "D"]:
                        st.write(
                            f"**{option}.** "
                            f"{item['options'][option]}"
                        )

                    st.divider()

        try:

            generated_questions = generate_questions(
                subject,
                difficulty,
                topic.strip(),
                show_question
            )

            st.session_state.assessment_questions = (
                generated_questions
            )

            st.session_state.assessment_subject = subject
            st.session_state.assessment_level = difficulty
            st.session_state.assessment_topic = topic.strip()

            current.success(
                "All 10 questions generated successfully!"
            )

            st.rerun()

        except requests.exceptions.ConnectionError:

            st.error(
                "Cannot connect to Ollama. Make sure Ollama is running."
            )

        except requests.exceptions.Timeout:

            st.error(
                "AI is taking too long. Please try again."
            )

        except requests.exceptions.HTTPError as error:

            st.error(f"Ollama request failed: {error}")

        except Exception as error:

            st.error(
                f"Unable to generate assessment: {error}"
            )

    # Display assessment

    questions = st.session_state.assessment_questions

    if questions:

        st.divider()
        st.subheader("Your Assessment")

        st.write(
            f"Subject: **{st.session_state.assessment_subject}**"
        )

        st.write(
            f"Difficulty: **{st.session_state.assessment_level}**"
        )

        with st.form(
            f"assessment_form_{st.session_state.assessment_version}"
        ):

            selected_answers = {}

            for index, question in enumerate(questions):

                st.markdown(f"### Question {index + 1}")
                st.write(question["question"])

                choices = [
                    f"{key}. {question['options'][key]}"
                    for key in ["A", "B", "C", "D"]
                ]

                selected = st.radio(
                    "Choose your answer:",
                    choices,
                    key=(
                        f"assessment_"
                        f"{st.session_state.assessment_version}_{index}"
                    ),
                    index=None
                )

                if selected:
                    selected_answers[index] = selected[0]

                st.divider()

            submitted = st.form_submit_button(
                "Submit Assessment",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if len(selected_answers) != TOTAL_QUESTIONS:

                st.warning("Please answer all 10 questions.")

            else:

                score = 0
                incorrect = []

                for index, question in enumerate(questions):

                    student = selected_answers[index]
                    correct = question["correct_answer"]

                    if student == correct:
                        score += 1

                    else:

                        incorrect.append({
                            "question": question["question"],
                            "correct_answer": (
                                f"{correct}. "
                                f"{question['options'][correct]}"
                            ),
                            "student_answer": (
                                f"{student}. "
                                f"{question['options'][student]}"
                            )
                        })

                st.session_state.assessment_answers = (
                    selected_answers
                )

                st.session_state.assessment_result = {
                    "score": score,
                    "total": TOTAL_QUESTIONS,
                    "incorrect_answers": incorrect
                }

                try:

                    save_assessment_to_database(
                        st.session_state.assessment_subject,
                        st.session_state.assessment_level,
                        st.session_state.get(
                            "assessment_topic", ""
                        ),
                        questions,
                        selected_answers,
                        score
                    )

                    st.session_state.assessment_saved = True
                    st.session_state.assessment_save_error = None

                except Exception as error:

                    st.session_state.assessment_saved = False
                    st.session_state.assessment_save_error = str(error)

                st.session_state.assessment_submitted = True

                st.rerun()

    # Results

    if st.session_state.assessment_submitted:

        result = st.session_state.assessment_result
        score = result["score"]

        percentage = score / TOTAL_QUESTIONS * 100

        st.divider()
        st.subheader("Assessment Result")

        st.markdown(f"""
        <div class="score-card">
            <h1>{score} / 10</h1>
            <h3>{percentage:.1f}%</h3>
            <p>Your Assessment Score</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.assessment_saved:

            st.success(
                "Assessment result saved permanently!"
            )

        else:

            st.error(
                "Assessment result could not be saved: "
                f"{st.session_state.assessment_save_error}"
            )

        if percentage >= 80:
            st.success("Excellent work!")

        elif percentage >= 60:
            st.info("Good effort! Keep practicing.")

        elif percentage >= 40:
            st.warning("You need more practice.")

        else:
            st.error(
                "Review the basic concepts and practice again."
            )

        st.subheader("Answer Review")

        for index, question in enumerate(questions):

            student = st.session_state.assessment_answers[index]
            correct = question["correct_answer"]

            st.markdown(
                f"**Question {index + 1}:** "
                f"{question['question']}"
            )

            if student == correct:

                st.success(
                    f"Correct: {correct}. "
                    f"{question['options'][correct]}"
                )

            else:

                st.error(
                    f"Your answer: {student}. "
                    f"{question['options'][student]}"
                )

                st.info(
                    f"Correct answer: {correct}. "
                    f"{question['options'][correct]}"
                )

            st.write(
                f"Explanation: {question['explanation']}"
            )

            st.divider()

        # AI Feedback

        st.subheader("AI Learning Feedback")

        if st.button(
            "Generate AI Feedback",
            use_container_width=True
        ):

            with st.spinner("Generating feedback..."):

                st.session_state.assessment_feedback = (
                    generate_feedback(
                        st.session_state.assessment_subject,
                        st.session_state.assessment_level,
                        score,
                        result["incorrect_answers"]
                    )
                )

        if "assessment_feedback" in st.session_state:

            st.write(
                st.session_state.assessment_feedback
            )

        # Retake

        if st.button(
            "Retake Assessment",
            use_container_width=True
        ):

            st.session_state.assessment_questions = []
            st.session_state.assessment_answers = {}
            st.session_state.assessment_submitted = False
            st.session_state.assessment_result = None
            st.session_state.assessment_saved = False
            st.session_state.assessment_save_error = None
            st.session_state.assessment_version += 1

            st.session_state.pop(
                "assessment_feedback", None
            )

            st.rerun()

    # Footer

    st.divider()

    st.markdown("""
    <div class="assessment-card">
        <h3>⚡ Powered by CampusMind AI</h3>
        <p>
            Local AI Model: Qwen 2.5 (1.5B)<br>
            AI Engine: Ollama<br>
            Assessment Type: Multiple Choice Questions<br>
            Generation: Objective-Based AI
        </p>
    </div>
    """, unsafe_allow_html=True)
    