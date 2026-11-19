import streamlit as st
import requests
import json
import re

from progress_database import (
    create_progress_tables,
    save_project_idea_history,
    get_project_idea_history
)


# ---------------- CONFIGURATION ----------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"


# ---------------- STUDENT ID ----------------

def get_student_id():

    student_id = st.session_state.get("logged_in_user_id")

    if student_id is None:
        student = st.session_state.get("student")

        if student:
            student_id = student[0]

    return int(student_id) if student_id is not None else None


# ---------------- COUNT GENERATED IDEAS ----------------

def count_generated_ideas(result, requested_count):

    headings = re.findall(
        r"(?im)^#{1,3}\s*Project\s+\d+\s*:",
        result
    )

    if headings:
        return len(headings)

    return requested_count


# ---------------- GENERATE PROJECT IDEAS ----------------

def generate_project_ideas(subject, level, category, count, interests):

    prompt = f"""
You are a professional university project advisor.

Generate exactly {count} different and practical project ideas.

Student Information:
Subject: {subject}
Skill Level: {level}
Project Category: {category}
Interests: {interests if interests else "Not specified"}

Instructions:
- Suggest realistic university-level projects.
- Match the student's skill level.
- Avoid repeating similar ideas.
- Use simple and clear English.
- Prefer projects that students can actually build.
- Do not give overly complicated ideas to beginners.

For EACH project, use this format:

## Project 1: Project Title

**Overview:**
Explain the project in simple words.

**Problem Statement:**
What problem does this project solve?

**Objectives:**
- Objective 1
- Objective 2
- Objective 3

**Main Features:**
- Feature 1
- Feature 2
- Feature 3
- Feature 4

**Recommended Technologies:**
Mention suitable programming languages, tools and technologies.

**Implementation Steps:**
1. First step
2. Second step
3. Third step
4. Fourth step

**Difficulty:** Beginner / Intermediate / Advanced

**Estimated Duration:** Mention a realistic duration.

Keep each project useful, practical and different.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert university project idea generator. "
                    "Give practical and clear project suggestions."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,
        "options": {
            "temperature": 0.7
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True,
        timeout=(10, 300)
    )

    response.raise_for_status()

    result = ""

    for line in response.iter_lines():

        if line:

            try:
                data = json.loads(line.decode("utf-8"))

                content = data.get("message", {}).get("content", "")

                if content:
                    result += content
                    yield result

                if data.get("done", False):
                    break

            except json.JSONDecodeError:
                continue


# ---------------- PROJECT HISTORY ----------------

def show_project_history():

    student_id = get_student_id()

    if student_id is None:
        st.info("Login to save and view your project idea history.")
        return

    try:

        history = get_project_idea_history(student_id)

        st.markdown("---")
        st.markdown("### 📚 Your Project Generation History")

        if not history:
            st.info("No project ideas generated yet.")
            return

        total_ideas = sum(
            row["idea_count"] for row in history
        )

        st.metric("Ideas in Recent History", total_ideas)

        for row in history:

            title = (
                f"{row['subject']} | "
                f"{row['idea_count']} Ideas | "
                f"{row['created_at']}"
            )

            with st.expander(title):

                st.write(f"**Skill Level:** {row['level']}")
                st.write(f"**Category:** {row['category']}")

                if row["interests"]:
                    st.write(f"**Interests:** {row['interests']}")

                st.markdown(row["generated_ideas"])

    except Exception as error:
        st.error(f"Unable to load project history: {error}")


# ---------------- MAIN PAGE ----------------

def render():

    create_progress_tables()

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">
            CAMPUSMIND AI • PROJECT DEVELOPMENT
        </div>
        <h1>AI Project Idea Generator</h1>
        <p>
        Discover practical and personalized project ideas
        according to your skills and interests.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 Project Preferences")

    col1, col2 = st.columns(2)

    with col1:

        subject = st.selectbox(
            "Select Subject",
            [
                "Python Programming",
                "Java",
                "C++",
                "Data Science",
                "Artificial Intelligence / Machine Learning",
                "Web Development",
                "Mobile App Development",
                "Computer Networks",
                "Database Management",
                "Information Technology",
                "Other"
            ]
        )

        level = st.selectbox(
            "Select Skill Level",
            [
                "Beginner",
                "Intermediate",
                "Advanced"
            ]
        )

    with col2:

        category = st.selectbox(
            "Select Project Category",
            [
                "Any Category",
                "AI / Machine Learning",
                "Web Application",
                "Desktop Software",
                "Mobile Application",
                "Data Analytics",
                "Database System",
                "Cybersecurity",
                "Education",
                "Other"
            ]
        )

        count = st.selectbox(
            "Number of Project Ideas",
            [1, 2, 3],
            index=1
        )

    interests = st.text_area(
        "Your Interests or Preferred Technologies (Optional)",
        placeholder="Example: Python, student management, automation, AI...",
        height=90
    )

    st.markdown("---")

    if st.button(
        "✨ Generate Project Ideas",
        use_container_width=True
    ):

        st.session_state.project_ideas_result = ""

        result_placeholder = st.empty()

        try:

            result = ""

            with st.spinner("AI is preparing your project ideas..."):

                for result in generate_project_ideas(
                    subject,
                    level,
                    category,
                    count,
                    interests
                ):

                    result_placeholder.markdown(result)

            st.session_state.project_ideas_result = result

            if result.strip():

                student_id = get_student_id()

                if student_id is not None:

                    idea_count = count_generated_ideas(
                        result,
                        count
                    )

                    save_project_idea_history(
                        student_id,
                        subject,
                        level,
                        category,
                        interests,
                        idea_count,
                        result
                    )

                    st.success(
                        f"{idea_count} project idea(s) generated and saved successfully!"
                    )

                else:

                    st.warning(
                        "Ideas generated, but login is required to save their history."
                    )

            else:

                st.warning(
                    "AI returned an empty response. Please try again."
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "Cannot connect to Ollama. Please make sure Ollama is running."
            )

            st.info(
                "Open another terminal and run: ollama run qwen2.5:1.5b"
            )

        except requests.exceptions.Timeout:

            st.error(
                "AI response took too long. Please try again."
            )

        except Exception as e:

            st.error(f"An error occurred: {e}")

    # Display generated ideas

    if st.session_state.get("project_ideas_result"):

        st.markdown("---")
        st.markdown("### 🚀 Your Generated Project Ideas")

        st.markdown(
            st.session_state.project_ideas_result
        )

    # Display saved history

    show_project_history()