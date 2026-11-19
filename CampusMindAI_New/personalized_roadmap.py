import streamlit as st
import requests
import json
import re
from difflib import SequenceMatcher
from progress_database import create_progress_tables, get_connection


# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"

DAILY_TIME_OPTIONS = [60, 90, 120]
DURATION_OPTIONS = [1, 2]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


# =========================================================
# SUBJECT PROGRESSION
# =========================================================

SUBJECT_PROGRESSIONS = {
    "Python Programming": [
        "Python syntax, variables, data types and operators",
        "Conditions, loops, collections, functions and a practical project"
    ],

    "Data Science": [
        "Python foundations, variables, data types, collections and functions",
        "NumPy, Pandas, CSV datasets, data cleaning and basic visualization"
    ],

    "Web Development": [
        "HTML fundamentals, document structure, headings, paragraphs, links, images, lists and forms",
        "CSS, selectors, colors, box model, Flexbox, Grid and responsive design"
    ],

    "C++ Programming": [
        "C++ structure, variables, data types, operators and input/output",
        "Conditions, loops, functions, arrays, strings and OOP fundamentals"
    ],

    "Java Programming": [
        "Java basics, JDK, variables, data types and operators",
        "Conditions, loops, methods, arrays, strings and OOP"
    ],

    "Machine Learning": [
        "ML introduction, types, datasets, features and labels",
        "Data preparation, cleaning, regression and classification basics"
    ],

    "Data Structures and Algorithms": [
        "Algorithms, complexity, arrays and strings",
        "Linked lists, stacks, queues, searching and sorting"
    ],

    "Computer Science": [
        "Computer science foundations, algorithms and data representation",
        "Programming concepts, data structures, operating systems and databases"
    ]
}


# =========================================================
# TIME CALCULATIONS
# =========================================================

def get_study_time(daily_time):

    total = int(daily_time * 0.80)

    learning = int(total * 0.25)
    practice = int(total * 0.40)
    exercise = int(total * 0.20)
    check = total - learning - practice - exercise

    return {
        "learning": learning,
        "practice": practice,
        "exercise": exercise,
        "check": check,
        "total": total
    }


def get_saturday_time(daily_time):

    total = int(daily_time * 0.80)

    revision = int(total * 0.30)
    quiz = int(total * 0.20)
    project = total - revision - quiz

    return {
        "revision": revision,
        "quiz": quiz,
        "project": project,
        "total": total
    }


# =========================================================
# TOPIC DUPLICATE VALIDATION
# =========================================================

def normalize_topic(topic):

    topic = str(topic).lower().strip()
    topic = re.sub(r"[^a-z0-9\s+#.]", " ", topic)
    topic = re.sub(r"\s+", " ", topic)

    return topic


def topics_are_similar(topic_a, topic_b):

    a = normalize_topic(topic_a)
    b = normalize_topic(topic_b)

    if not a or not b:
        return False

    if a == b:
        return True

    if SequenceMatcher(None, a, b).ratio() >= 0.88:
        return True

    stop_words = {
        "introduction", "basics", "basic", "fundamentals",
        "the", "and", "for", "with", "using", "to", "of"
    }

    words_a = set(a.split()) - stop_words
    words_b = set(b.split()) - stop_words

    if words_a and words_b:

        overlap = len(words_a & words_b) / len(words_a | words_b)

        if overlap >= 0.85:
            return True

    return False


# =========================================================
# WEEK VALIDATION
# =========================================================

def validate_week(week, week_number, previous_topics):

    if not isinstance(week, dict):
        raise ValueError("Invalid weekly data.")

    days = week.get("days")

    if not isinstance(days, list) or len(days) != 5:
        raise ValueError(f"Week {week_number} must have five days.")

    topics = []

    required = [
        "topic", "learning", "practice", "exercise", "check"
    ]

    for index, day in enumerate(days):

        if not isinstance(day, dict):
            raise ValueError("Invalid daily schedule.")

        if day.get("day") != DAYS[index]:
            raise ValueError("Incorrect weekday order.")

        for field in required:

            value = day.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Missing {field} in {DAYS[index]}.")

        topics.append(day["topic"].strip())

    # Check duplicate topics within the week.

    for i, topic in enumerate(topics):

        for earlier in topics[:i]:

            if topics_are_similar(topic, earlier):
                raise ValueError(f"Repeated topic: {topic}")

    # Check topics from previous weeks.

    for topic in topics:

        for earlier in previous_topics:

            if topics_are_similar(topic, earlier):
                raise ValueError(
                    f"Topic repeated from previous week: {topic}"
                )

    if not str(week.get("focus", "")).strip():
        raise ValueError("Weekly focus is missing.")

    if not str(week.get("outcome", "")).strip():
        raise ValueError("Weekly outcome is missing.")

    # Validate Saturday project.

    saturday_data = week.get("saturday")

    if not isinstance(saturday_data, dict):
        saturday_data = {}

    project = str(
        saturday_data.get("project", "")
    ).strip()

    if len(project) < 12:
        raise ValueError("Saturday mini-project is missing or too short.")

    for earlier in previous_topics:

        if topics_are_similar(project, earlier):
            raise ValueError(
                f"Saturday project repeated from previous week: {project}"
            )

    for topic in topics:

        if topics_are_similar(project, topic):
            raise ValueError(
                f"Saturday project duplicates this week's topic: {project}"
            )

    topic_text = ", ".join(topics)

    week["saturday"] = {
        "revision": f"Revise all five topics: {topic_text}.",
        "quiz": f"Complete a weekly quiz covering: {topic_text}.",
        "project": project
    }

    return week


# =========================================================
# WEEK STAGE
# =========================================================

def get_week_stage(subject, duration, week_number):

    progression = SUBJECT_PROGRESSIONS.get(subject)

    if not progression:

        progression = [
            f"Foundations and basic concepts of {subject}",
            f"Core skills and practical concepts of {subject}"
        ]

    if duration == 1:

        return (
            f"Create a compact beginner-friendly learning plan "
            f"for {subject}. Cover essential concepts and practical skills."
        )

    return progression[week_number - 1]


# =========================================================
# AI WEEK GENERATION
# =========================================================

def generate_one_week(
    goal,
    subject,
    level,
    daily_time,
    duration,
    week_number,
    previous_topics
):

    stage = get_week_stage(
        subject,
        duration,
        week_number
    )

    previous_text = "\n".join(
        f"- {topic}" for topic in previous_topics
    )

    if not previous_text:
        previous_text = "No previous topics or projects."

    last_error = None

    for attempt in range(3):

        retry_instruction = ""

        if attempt > 0:

            retry_instruction = f"""
IMPORTANT CORRECTION:

Your previous response was rejected because:

{last_error}

Generate completely different topics.
Do not repeat the rejected topic or any previous topic.
Choose a different practical project.
"""

        prompt = f"""
Create Week {week_number} of a {duration}-week learning roadmap.

Goal: {goal}
Subject: {subject}
Level: {level}
Daily maximum: {daily_time} minutes.

This week's learning stage:
{stage}

PREVIOUSLY COVERED TOPICS AND PROJECTS:
{previous_text}

{retry_instruction}

STRICT RULES:

- Exactly five days: Monday to Friday.
- Five different and relevant topics.
- Never repeat previous topics.
- Never repeat a previous week's project.
- Do not use a previous project name as a daily topic.
- Follow the exact weekly learning stage.
- Follow logical learning progression.
- Keep activities practical and suitable for the selected level.
- Learning, practice, exercise and check must be different.
- Saturday project must be new and use this week's skills.
- Use simple English.
- Return valid JSON only.

JSON structure:

{{
 "week": {week_number},
 "focus": "Weekly focus",
 "days": [
  {{
   "day": "Monday",
   "topic": "Topic name",
   "learning": "Short learning activity",
   "practice": "Practical task",
   "exercise": "Exercise",
   "check": "Knowledge check"
  }},
  {{
   "day": "Tuesday",
   "topic": "Topic name",
   "learning": "Short learning activity",
   "practice": "Practical task",
   "exercise": "Exercise",
   "check": "Knowledge check"
  }},
  {{
   "day": "Wednesday",
   "topic": "Topic name",
   "learning": "Short learning activity",
   "practice": "Practical task",
   "exercise": "Exercise",
   "check": "Knowledge check"
  }},
  {{
   "day": "Thursday",
   "topic": "Topic name",
   "learning": "Short learning activity",
   "practice": "Practical task",
   "exercise": "Exercise",
   "check": "Knowledge check"
  }},
  {{
   "day": "Friday",
   "topic": "Topic name",
   "learning": "Short learning activity",
   "practice": "Practical task",
   "exercise": "Exercise",
   "check": "Knowledge check"
  }}
 ],
 "saturday": {{
  "project": "A new realistic mini project"
 }},
 "outcome": "Expected weekly learning outcome"
}}
"""

        try:

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a professional curriculum designer. "
                                "Create unique, progressive learning content. "
                                "Never repeat previous topics or projects. "
                                "Return valid JSON only."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "format": "json",
                    "stream": False,
                    "keep_alive": "10m",
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 1400
                    }
                },
                timeout=(10, 240)
            )

            response.raise_for_status()

            content = response.json()["message"]["content"]

            week = json.loads(content)

            week = validate_week(
                week,
                week_number,
                previous_topics
            )

            return week

        except (ValueError, KeyError, TypeError) as error:

            last_error = str(error)

        except requests.exceptions.RequestException:
            raise

    raise ValueError(
        f"Week {week_number} generation failed after 3 attempts: "
        f"{last_error}"
    )


# =========================================================
# COMPLETE AI ROADMAP
# =========================================================

def generate_ai_roadmap(
    goal,
    subject,
    level,
    daily_time,
    duration,
    progress_callback=None
):

    weeks = []
    previous_topics = []

    for week_number in range(1, duration + 1):

        week = generate_one_week(
            goal,
            subject,
            level,
            daily_time,
            duration,
            week_number,
            previous_topics
        )

        weeks.append(week)

        previous_topics.extend(
            day["topic"] for day in week["days"]
        )

        previous_topics.append(
            week["saturday"]["project"]
        )

        if progress_callback:

            progress_callback(
                week_number,
                duration
            )

    return {"weeks": weeks}


# =========================================================
# FIXED DATA SCIENCE BEGINNER TWO-WEEK PLAN
# =========================================================

def get_fixed_data_science_plan():

    week1 = [
        (
            "Introduction to Python and Data Science",
            "Understand Python, Data Science and their uses.",
            "Write your first Python program using print().",
            "Display your name and three uses of Data Science.",
            "Explain Python and Data Science with examples."
        ),
        (
            "Python Variables and Data Types",
            "Learn variables, integers, floats, strings and booleans.",
            "Create student variables and use type().",
            "Build a student information program.",
            "Identify common Python data types."
        ),
        (
            "Python Lists, Tuples and Dictionaries",
            "Understand Python collections.",
            "Create a list, tuple and dictionary.",
            "Build a student record using a dictionary.",
            "Explain the difference between collections."
        ),
        (
            "Python Conditions and Loops",
            "Learn if, elif, else, for and while.",
            "Write a pass/fail program.",
            "Check five student results using conditions.",
            "Explain conditions and loops."
        ),
        (
            "Python Functions and Basic Problem Solving",
            "Learn functions, parameters and return values.",
            "Create functions for total and average marks.",
            "Build a marks calculator using functions.",
            "Explain why functions are useful."
        )
    ]

    week2 = [
        (
            "Introduction to NumPy Arrays",
            "Understand NumPy and numerical computing.",
            "Create arrays using np.array().",
            "Calculate sum, mean and maximum of marks.",
            "Explain NumPy arrays."
        ),
        (
            "Pandas Series and DataFrames",
            "Understand Pandas Series and DataFrames.",
            "Create a Series and a DataFrame.",
            "Build a student DataFrame.",
            "Differentiate Series and DataFrame."
        ),
        (
            "Loading and Inspecting CSV Datasets",
            "Understand CSV files and read_csv().",
            "Use head(), tail(), shape and columns.",
            "Load and inspect a sample student CSV.",
            "Explain read_csv() and head()."
        ),
        (
            "Data Cleaning and Missing Values",
            "Understand missing values and data cleaning.",
            "Use isnull(), fillna() and dropna().",
            "Clean a student dataset with missing marks.",
            "Compare fillna() and dropna()."
        ),
        (
            "Exploratory Data Analysis and Visualization",
            "Understand EDA and descriptive statistics.",
            "Use describe() and create a chart.",
            "Analyze student marks with a bar chart.",
            "Explain why EDA is useful."
        )
    ]

    def build_week(number, focus, topics, outcome, project):

        days = []

        for index, item in enumerate(topics):

            days.append({
                "day": DAYS[index],
                "topic": item[0],
                "learning": item[1],
                "practice": item[2],
                "exercise": item[3],
                "check": item[4]
            })

        topic_text = ", ".join(
            day["topic"] for day in days
        )

        return {
            "week": number,
            "focus": focus,
            "days": days,
            "saturday": {
                "revision": f"Revise all five topics: {topic_text}.",
                "quiz": f"Complete a weekly quiz covering: {topic_text}.",
                "project": project
            },
            "outcome": outcome
        }

    return [
        build_week(
            1,
            "Python Fundamentals for Data Science",
            week1,
            "Understand Python fundamentals and write small programs using variables, collections, conditions, loops and functions.",
            "Create a Student Marks Management program. Store names and marks, calculate averages and display pass or fail results."
        ),
        build_week(
            2,
            "Introduction to Data Science Tools",
            week2,
            "Work with NumPy, Pandas, CSV datasets, missing values and basic exploratory data analysis.",
            "Create a Student Dataset Analysis project. Load a CSV, clean missing marks and create a chart."
        )
    ]


# =========================================================
# ROADMAP ROUTER
# =========================================================

def generate_roadmap(
    goal,
    subject,
    level,
    daily_time,
    duration,
    progress_callback=None
):

    if duration not in DURATION_OPTIONS:
        raise ValueError("Select a roadmap duration of 1 or 2 weeks.")

    if (
        subject == "Data Science"
        and level == "Beginner"
        and duration == 2
    ):

        data = {
            "weeks": get_fixed_data_science_plan()
        }

        if progress_callback:

            for number in range(1, duration + 1):
                progress_callback(number, duration)

        return data

    return generate_ai_roadmap(
        goal,
        subject,
        level,
        daily_time,
        duration,
        progress_callback
    )


# =========================================================
# ROADMAP FORMATTER
# =========================================================

def format_roadmap(data, daily_time, duration):

    output = [
        "# Personalized Learning Roadmap",
        "",
        f"**Duration:** {duration} Weeks",
        f"**Maximum Daily Study Time:** {daily_time} Minutes",
        ""
    ]

    for week in data["weeks"]:

        output.extend([
            "---",
            "",
            f"## Week {week['week']}: {week['focus']}",
            ""
        ])

        times = get_study_time(daily_time)

        for day in week["days"]:

            output.extend([
                f"### {day['day']}",
                "",
                f"**Topic:** {day['topic']}",
                "",
                f"- Learning ({times['learning']} min): {day['learning']}",
                f"- Practical Work ({times['practice']} min): {day['practice']}",
                f"- Exercise ({times['exercise']} min): {day['exercise']}",
                f"- Knowledge Check ({times['check']} min): {day['check']}",
                "",
                f"**Daily Total: {times['total']} / {daily_time} minutes**",
                ""
            ])

        saturday = week["saturday"]
        sat = get_saturday_time(daily_time)

        output.extend([
            "### Saturday: Weekly Revision",
            "",
            f"- Revision ({sat['revision']} min): {saturday['revision']}",
            f"- Quiz ({sat['quiz']} min): {saturday['quiz']}",
            f"- Mini-Project ({sat['project']} min): {saturday['project']}",
            "",
            f"**Daily Total: {sat['total']} / {daily_time} minutes**",
            "",
            "### Sunday: Rest Day",
            "",
            "No study tasks. Take a break and relax.",
            "",
            "### Weekly Learning Outcome",
            "",
            week["outcome"],
            ""
        ])

    return "\n".join(output)


# =========================================================
# SAVE ROADMAP TO STUDENT DATABASE
# =========================================================

def save_roadmap_to_database(
    data, goal, subject, level, daily_time, duration
):

    student_id = st.session_state.get("logged_in_user_id")

    if student_id is None:
        raise ValueError("Please log in before saving your roadmap.")

    create_progress_tables()
    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            INSERT INTO roadmap_records
            (student_id, goal, subject, level, daily_time,
             duration_weeks, roadmap_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(student_id),
                goal,
                subject,
                level,
                int(daily_time),
                int(duration),
                json.dumps(data, ensure_ascii=False)
            )
        )

        roadmap_id = cursor.lastrowid
        activity_rows = []

        for week in data.get("weeks", []):

            week_number = int(week.get("week", 1))

            for day in week.get("days", []):

                activity_rows.append((
                    roadmap_id,
                    week_number,
                    str(day.get("day", "")),
                    str(day.get("topic", "")).strip()
                ))

            saturday = week.get("saturday", {})
            project = str(saturday.get("project", "")).strip()

            if project:

                activity_rows.append((
                    roadmap_id,
                    week_number,
                    "Saturday",
                    project
                ))

        if activity_rows:

            conn.executemany(
                """
                INSERT INTO roadmap_topics
                (roadmap_id, week_number, day_name, topic)
                VALUES (?, ?, ?, ?)
                """,
                activity_rows
            )

        conn.commit()

        return roadmap_id

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# =========================================================
# STREAMLIT INTERFACE
# =========================================================

def render():

    st.markdown(
        """
        <div class="hero">
            <div class="hero-tag">
                AI POWERED • PERSONALIZED LEARNING
            </div>
            <h1>🗺️ Personalized Learning Roadmap</h1>
            <p>
                Create your personal learning journey with AI guidance.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 🎯 Define Your Learning Goal")

    goal = st.text_input(
        "What do you want to achieve?",
        placeholder="Example: Become a Python Developer"
    )

    subject = st.selectbox(
        "Select Subject / Skill",
        [
            "Python Programming",
            "C++ Programming",
            "Java Programming",
            "Data Science",
            "Machine Learning",
            "Web Development",
            "Data Structures and Algorithms",
            "Computer Science",
            "Other"
        ]
    )

    level = st.selectbox(
        "Current Knowledge Level",
        ["Beginner", "Intermediate", "Advanced"]
    )

    col1, col2 = st.columns(2)

    with col1:

        daily_time = st.selectbox(
            "Maximum Daily Study Time (Minutes)",
            DAILY_TIME_OPTIONS,
            index=1
        )

    with col2:

        duration = st.selectbox(
            "Roadmap Duration (Weeks)",
            DURATION_OPTIONS,
            index=1
        )

    if st.button(
        "🚀 Generate My Learning Roadmap",
        use_container_width=True
    ):

        if not goal.strip():

            st.warning("Please enter your learning goal.")

        else:

            st.session_state.pop("learning_roadmap", None)
            st.session_state.pop("roadmap_settings", None)

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total):

                percent = int((current / total) * 100)

                progress_bar.progress(percent)

                status_text.info(
                    f"Generating Week {current} of {total}... "
                    f"{percent}% completed"
                )

            try:

                status_text.info(
                    "Preparing your personalized learning roadmap..."
                )

                data = generate_roadmap(
                    goal.strip(),
                    subject,
                    level,
                    daily_time,
                    duration,
                    update_progress
                )

                roadmap = format_roadmap(
                    data,
                    daily_time,
                    duration
                )

                # Save roadmap and its topics to SQLite.

                try:

                    save_roadmap_to_database(
                        data,
                        goal.strip(),
                        subject,
                        level,
                        daily_time,
                        duration
                    )

                    st.success(
                        "Roadmap saved to your learning progress."
                    )

                except Exception as save_error:

                    st.warning(
                        "Your roadmap was generated, but it could not be "
                        f"saved to the progress dashboard: {save_error}"
                    )

                st.session_state["learning_roadmap"] = roadmap

                st.session_state["roadmap_settings"] = {
                    "goal": goal.strip(),
                    "subject": subject,
                    "level": level,
                    "daily_time": daily_time,
                    "duration": duration
                }

                progress_bar.progress(100)
                status_text.success("Your roadmap is ready!")

                st.success(
                    "Personalized roadmap generated successfully!"
                )

            except requests.exceptions.ConnectionError:

                status_text.empty()

                st.error(
                    "Ollama is not running. Please start Ollama."
                )

            except requests.exceptions.Timeout:

                status_text.empty()

                st.error(
                    "AI generation timed out. Please try again."
                )

            except requests.exceptions.RequestException as error:

                status_text.empty()

                st.error(f"Ollama request failed: {error}")

            except Exception as error:

                status_text.empty()

                st.error(f"Roadmap generation failed: {error}")

    if st.session_state.get("learning_roadmap"):

        st.markdown("---")
        st.markdown("### 📚 Your Personalized Learning Roadmap")

        settings = st.session_state.get("roadmap_settings", {})

        if settings:

            st.caption(
                f"{settings['subject']} • "
                f"{settings['level']} • "
                f"{settings['duration']} Weeks"
            )

        st.markdown(
            st.session_state["learning_roadmap"]
        )

        st.download_button(
            "📥 Download Roadmap",
            data=st.session_state["learning_roadmap"],
            file_name="CampusMind_Learning_Roadmap.md",
            mime="text/markdown",
            use_container_width=True
        )