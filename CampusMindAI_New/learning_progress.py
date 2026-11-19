
import streamlit as st
import pandas as pd

from progress_database import create_progress_tables, get_connection


# =====================================================
# DATABASE HELPERS
# =====================================================

def get_student_id():
    student_id = st.session_state.get("logged_in_user_id")

    if student_id is None:
        student = st.session_state.get("student")

        if student:
            student_id = student[0]

    return int(student_id) if student_id is not None else None


def get_assessment_data(student_id):
    create_progress_tables()
    conn = get_connection()

    try:
        attempts = conn.execute(
            """
            SELECT id, subject, difficulty, selected_topic,
                   score, total_questions, percentage, created_at
            FROM assessment_attempts
            WHERE student_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (student_id,)
        ).fetchall()

        topic_results = conn.execute(
            """
            SELECT qr.topic,
                   COUNT(*) AS total_questions,
                   SUM(qr.is_correct) AS correct_answers
            FROM assessment_question_results qr
            JOIN assessment_attempts a
                ON a.id = qr.attempt_id
            WHERE a.student_id = ?
            GROUP BY qr.topic
            ORDER BY qr.topic
            """,
            (student_id,)
        ).fetchall()

        return attempts, topic_results

    finally:
        conn.close()


def get_roadmap_data(student_id):
    conn = get_connection()

    try:
        roadmaps = conn.execute(
            """
            SELECT id, goal, subject, level,
                   daily_time, duration_weeks, created_at
            FROM roadmap_records
            WHERE student_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (student_id,)
        ).fetchall()

        return roadmaps

    finally:
        conn.close()


def get_roadmap_topics(roadmap_id):
    conn = get_connection()

    try:
        topics = conn.execute(
            """
            SELECT id, week_number, day_name, topic, status
            FROM roadmap_topics
            WHERE roadmap_id = ?
            ORDER BY week_number,
                CASE day_name
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    ELSE 7
                END,
                id
            """,
            (roadmap_id,)
        ).fetchall()

        return topics

    finally:
        conn.close()


def update_topic_status(topic_id, student_id, completed):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE roadmap_topics
            SET status = ?,
                completed_at = CASE
                    WHEN ? = 'Completed' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            WHERE id = ?
            AND roadmap_id IN (
                SELECT id
                FROM roadmap_records
                WHERE student_id = ?
            )
            """,
            (
                "Completed" if completed else "Pending",
                "Completed" if completed else "Pending",
                topic_id,
                student_id
            )
        )

        conn.commit()

    finally:
        conn.close()


# =====================================================
# DASHBOARD
# =====================================================

def render():

    st.markdown("""
    <div style="
        background:linear-gradient(120deg,#2563eb,#7c3aed);
        padding:26px;
        border-radius:18px;
        color:white;
        margin-bottom:22px;">
        <h1 style="color:white;margin:0;">
            📊 Learning Progress & Topic Mastery
        </h1>
        <p style="color:#e0e7ff;margin:8px 0 0;">
            Track your assessment performance and learning journey.
        </p>
    </div>
    """, unsafe_allow_html=True)

    student_id = get_student_id()

    if student_id is None:
        st.warning("Please log in to view your personal learning progress.")
        return

    try:
        attempts, topic_results = get_assessment_data(student_id)
        roadmaps = get_roadmap_data(student_id)

    except Exception as error:
        st.error(f"Unable to load progress data: {error}")
        return

    # -------------------------------------------------
    # PERFORMANCE CALCULATIONS
    # -------------------------------------------------

    total_tests = len(attempts)

    if total_tests:
        percentages = [float(row["percentage"]) for row in attempts]

        average_score = sum(percentages) / total_tests
        best_score = max(percentages)

        total_correct = sum(
            int(row["score"]) for row in attempts
        )

        total_questions = sum(
            int(row["total_questions"]) for row in attempts
        )

    else:
        average_score = 0
        best_score = 0
        total_correct = 0
        total_questions = 0

    mastered_topics = 0

    for row in topic_results:
        total = int(row["total_questions"])
        correct = int(row["correct_answers"] or 0)

        if total and (correct / total) >= 0.80:
            mastered_topics += 1

    overall_accuracy = (
        total_correct / total_questions * 100
        if total_questions else 0
    )

    # -------------------------------------------------
    # TOP METRICS
    # -------------------------------------------------

    st.subheader("Performance Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Assessments Taken", total_tests)
    c2.metric("Average Score", f"{average_score:.1f}%")
    c3.metric("Best Score", f"{best_score:.1f}%")
    c4.metric("Topics Mastered", mastered_topics)

    st.progress(overall_accuracy / 100)

    st.caption(
        f"Overall question accuracy: {overall_accuracy:.1f}%"
    )

    st.divider()

    # -------------------------------------------------
    # ASSESSMENT HISTORY
    # -------------------------------------------------

    st.subheader("📝 Assessment History")

    if attempts:

        history_data = []

        for row in attempts:
            history_data.append({
                "Subject": row["subject"],
                "Difficulty": row["difficulty"],
                "Score": f"{row['score']}/{row['total_questions']}",
                "Percentage": f"{float(row['percentage']):.1f}%",
                "Date": row["created_at"]
            })

        # Static table instead of canvas-based dataframe
        history_df = pd.DataFrame(history_data)

        st.table(history_df)

    else:
        st.info(
            "No assessment records yet. Complete a Smart Skill Assessment to see your results here."
        )

    st.divider()

    # -------------------------------------------------
    # TOPIC MASTERY
    # -------------------------------------------------

    st.subheader("🎯 Topic Mastery")

    if topic_results:

        for row in topic_results:

            total = int(row["total_questions"])
            correct = int(row["correct_answers"] or 0)

            accuracy = (
                correct / total * 100
                if total else 0
            )

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{row['topic']}**")
                st.progress(accuracy / 100)

            with col2:
                st.write(f"{accuracy:.1f}%")
                st.caption(f"{correct}/{total} correct")

            if accuracy >= 80:
                st.caption("Status: Strong topic")
            elif accuracy >= 50:
                st.caption("Status: Developing")
            else:
                st.caption("Status: Needs practice")

            st.markdown("---")

    else:
        st.info(
            "Topic mastery will appear after you complete an assessment."
        )

    # -------------------------------------------------
    # ROADMAP PROGRESS
    # -------------------------------------------------

    st.subheader("🗺️ Learning Roadmap Progress")

    if not roadmaps:

        st.info(
            "No saved roadmaps found. Generate a roadmap to start tracking your learning progress."
        )

    else:

        roadmap_options = {
            (
                f"{row['subject']} — {row['goal']} "
                f"({row['duration_weeks']} weeks)"
            ): int(row["id"])
            for row in roadmaps
        }

        selected_label = st.selectbox(
            "Select Your Roadmap",
            list(roadmap_options.keys())
        )

        roadmap_id = roadmap_options[selected_label]

        topics = get_roadmap_topics(roadmap_id)

        if not topics:

            st.info("No topics are available in this roadmap.")

        else:

            completed = sum(
                1 for row in topics
                if row["status"] == "Completed"
            )

            total = len(topics)

            percentage = (
                completed / total * 100
                if total else 0
            )

            c1, c2, c3 = st.columns(3)

            c1.metric("Total Activities", total)
            c2.metric("Completed", completed)
            c3.metric("Remaining", total - completed)

            st.progress(percentage / 100)

            st.caption(
                f"Roadmap Completion: {percentage:.1f}%"
            )

            st.markdown("### Update Your Learning Activities")

            for row in topics:

                label = (
                    f"Week {row['week_number']} | "
                    f"{row['day_name']} | {row['topic']}"
                )

                is_completed = row["status"] == "Completed"

                col1, col2 = st.columns([5, 1])

                with col1:
                    st.write(label)

                with col2:

                    if is_completed:

                        if st.button(
                            "Undo",
                            key=f"undo_{row['id']}"
                        ):
                            update_topic_status(
                                row["id"],
                                student_id,
                                False
                            )
                            st.rerun()

                        st.caption("Completed")

                    else:

                        if st.button(
                            "Complete",
                            key=f"complete_{row['id']}"
                        ):
                            update_topic_status(
                                row["id"],
                                student_id,
                                True
                            )
                            st.rerun()

    st.divider()

    st.caption(
        "CampusMind AI • Personal Learning Analytics"
    )
