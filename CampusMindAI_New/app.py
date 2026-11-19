
import streamlit as st
import html
import textwrap

import student_profile
import ai_mentor
import smart_assessment
import personalized_roadmap
import learning_progress
import project_idea_generator

from progress_database import create_progress_tables, get_connection


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="CampusMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

PAGES = [
    "Dashboard",
    "Student Profile",
    "AI Personal Learning Mentor",
    "Smart Skill Assessment",
    "Personalized Learning Roadmap",
    "Learning Progress & Topic Mastery",
    "AI Project Idea Generator"
]

PAGE_ICONS = {
    "Dashboard": "⌂",
    "Student Profile": "♙",
    "AI Personal Learning Mentor": "✦",
    "Smart Skill Assessment": "◎",
    "Personalized Learning Roadmap": "⌁",
    "Learning Progress & Topic Mastery": "▥",
    "AI Project Idea Generator": "✧"
}


# ---------------- HTML HELPER ----------------

def render_html(content):
    st.html(textwrap.dedent(content))


# ---------------- STUDENT HELPERS ----------------

def get_student_id():
    student_id = st.session_state.get("logged_in_user_id")

    if student_id is None:
        student = st.session_state.get("student")
        if student:
            student_id = student[0]

    try:
        return int(student_id) if student_id is not None else None
    except (TypeError, ValueError):
        return None


def get_student_name():
    student_id = get_student_id()

    if student_id is not None:
        try:
            student_profile.create_database()

            with student_profile.get_connection() as conn:
                student = conn.execute(
                    "SELECT full_name FROM students WHERE id = ?",
                    (student_id,)
                ).fetchone()

            if student:
                return student["full_name"]

        except Exception:
            pass

    for key in ["student_name", "logged_in_user_name", "name"]:
        value = st.session_state.get(key)
        if value:
            return str(value)

    return "Student"


# ---------------- DASHBOARD DATABASE ----------------

def get_dashboard_stats(student_id):
    create_progress_tables()
    conn = get_connection()

    try:
        assessments = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM assessment_attempts
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()["total"]

        topic_rows = conn.execute(
            """
            SELECT qr.topic,
                   COUNT(*) AS total_questions,
                   SUM(qr.is_correct) AS correct_answers
            FROM assessment_question_results qr
            JOIN assessment_attempts a ON a.id = qr.attempt_id
            WHERE a.student_id = ?
            GROUP BY qr.topic
            """,
            (student_id,)
        ).fetchall()

        mastered_topics = sum(
            1 for row in topic_rows
            if row["total_questions"] > 0
            and (row["correct_answers"] or 0) / row["total_questions"] >= 0.50
        )

        roadmap_stats = conn.execute(
            """
            SELECT COUNT(rt.id) AS total,
                   SUM(
                       CASE WHEN rt.status = 'Completed'
                       THEN 1 ELSE 0 END
                   ) AS completed
            FROM roadmap_records rr
            LEFT JOIN roadmap_topics rt ON rt.roadmap_id = rr.id
            WHERE rr.student_id = ?
            """,
            (student_id,)
        ).fetchone()

        total = roadmap_stats["total"] or 0
        completed = roadmap_stats["completed"] or 0
        progress = completed / total * 100 if total else 0

        project_stats = conn.execute(
            """
            SELECT COALESCE(SUM(idea_count), 0) AS total
            FROM project_idea_history
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

        return {
            "assessments": assessments or 0,
            "mastered_topics": mastered_topics,
            "learning_progress": progress,
            "projects_generated": project_stats["total"] or 0
        }

    finally:
        conn.close()


# ---------------- PAGE NAVIGATION ----------------

def open_page(target):
    # Store the destination separately.
    # Do not modify the radio widget's state after it is created.
    st.session_state["pending_navigation_page"] = target
    st.rerun()


# ---------------- PREMIUM UI DESIGN ----------------

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(ellipse at 5% 0%, #242B55 0%, transparent 34%),
        radial-gradient(ellipse at 95% 30%, #251F48 0%, transparent 30%),
        #0B1020;
    color: #F5F6FF;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1550px;
    padding: 1.6rem 2.5rem 3rem !important;
}

/* Sidebar */

[data-testid="stSidebar"] {
    background: #10172B;
    border-right: 1px solid #293654;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem;
}

.brand {
    font-size: 25px;
    font-weight: 900;
    letter-spacing: -1px;
    color: #FFFFFF;
}

.brand span {
    color: #A895FF;
}

.brand-symbol {
    color: #A895FF;
    font-size: 22px;
}

.brand-sub {
    color: #8793B3;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-top: 5px;
    margin-bottom: 32px;
}

.nav-heading {
    color: #7784A7;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.8px;
    margin: 18px 0 12px;
}

[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 7px;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 11px 12px;
    border-radius: 11px;
    border: 1px solid transparent;
    background: transparent;
    transition: 0.2s ease;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #202B48;
    border-color: #354365;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(100deg, #37366F, #292E55);
    border-color: #7068C5;
}

[data-testid="stSidebar"] div[role="radiogroup"] label p {
    color: #E9ECFA !important;
    font-size: 12px;
    font-weight: 650;
}

.sidebar-info {
    margin-top: 32px;
    padding: 16px;
    border-radius: 14px;
    background: linear-gradient(145deg, #20294A, #1A203A);
    border: 1px solid #354061;
}

.sidebar-info-title {
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 800;
}

.sidebar-info-text {
    color: #AAB4D0;
    font-size: 10px;
    line-height: 1.8;
    margin-top: 8px;
}

/* Top Header */

.top-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 13px 19px;
    margin-bottom: 22px;
    border-radius: 15px;
    background: rgba(24, 34, 59, 0.85);
    border: 1px solid #354363;
}

.top-brand {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 850;
    letter-spacing: .3px;
}

.top-brand span {
    color: #A995FF;
}

.top-caption {
    color: #909DBB;
    font-size: 10px;
    margin-top: 3px;
}

.profile-chip {
    background: #30345D;
    color: #E6E3FF;
    padding: 9px 15px;
    border: 1px solid #565B91;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 750;
}

/* Hero */

.hero-new {
    position: relative;
    overflow: hidden;
    padding: 34px;
    border-radius: 23px;
    border: 1px solid #625CA9;
    background:
        radial-gradient(circle at 90% 10%, rgba(180,145,255,.30), transparent 30%),
        linear-gradient(120deg, #303B78 0%, #4C438D 55%, #65469A 100%);
    min-height: 270px;
}

.hero-eyebrow {
    color: #D3CDFF;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 2.2px;
    margin-bottom: 15px;
}

.hero-title {
    color: #FFFFFF;
    font-size: 34px;
    font-weight: 900;
    line-height: 1.2;
    letter-spacing: -1.3px;
    margin-bottom: 12px;
}

.hero-description {
    color: #E0DEFF;
    font-size: 12px;
    line-height: 1.9;
    max-width: 560px;
}

.hero-tag {
    display: inline-block;
    margin-top: 19px;
    padding: 8px 14px;
    border-radius: 30px;
    border: 1px solid rgba(255,255,255,.25);
    background: rgba(255,255,255,.12);
    color: #FFFFFF;
    font-size: 10px;
    font-weight: 750;
}

.hero-side-icon {
    font-size: 31px;
    margin-bottom: 12px;
}

.hero-side-title {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 850;
    margin-bottom: 8px;
}

.hero-side-text {
    color: #D6D3F5;
    font-size: 11px;
    line-height: 1.8;
}

.hero-side-label {
    color: #D7CCFF;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin-top: 18px;
}

/* Sections */

.section-heading {
    color: #F7F8FF;
    font-size: 20px;
    font-weight: 850;
    letter-spacing: -.4px;
    margin: 30px 0 4px;
}

.section-description {
    color: #929DBB;
    font-size: 11px;
    margin-bottom: 17px;
}

/* Statistics */

.stat-card {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, #202C49, #172139);
    border: 1px solid #354563;
    border-radius: 17px;
    padding: 19px;
    min-height: 155px;
    box-shadow: 0 9px 24px rgba(0,0,0,.14);
    transition: .2s ease;
}

.stat-card:hover {
    transform: translateY(-3px);
    border-color: #7771C9;
}

.stat-icon {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    font-size: 21px;
}

.stat-label {
    color: #AAB5D0;
    font-size: 11px;
    font-weight: 650;
    margin-top: 14px;
}

.stat-value {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: 900;
    margin-top: 2px;
}

/* Learning Panels */

.learning-panel {
    background: linear-gradient(145deg, #202B49, #182139);
    border: 1px solid #374564;
    border-radius: 18px;
    padding: 23px;
    min-height: 205px;
}

.panel-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.panel-title {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 850;
}

.panel-tag {
    color: #BFB7FF;
    background: #33345F;
    border: 1px solid #55558D;
    padding: 5px 9px;
    border-radius: 20px;
    font-size: 9px;
    font-weight: 750;
}

.panel-description {
    color: #A8B3CE;
    font-size: 11px;
    line-height: 1.8;
}

.progress-track {
    height: 11px;
    border-radius: 20px;
    background: #303B5A;
    overflow: hidden;
    margin: 20px 0 12px;
}

.progress-fill {
    height: 11px;
    border-radius: 20px;
    background: linear-gradient(90deg, #7186FF, #B18AFF);
}

.progress-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.progress-number {
    color: white;
    font-size: 25px;
    font-weight: 900;
}

.mini-label {
    color: #919DBB;
    font-size: 9px;
    letter-spacing: .7px;
}

.action-item {
    display: flex;
    gap: 13px;
    align-items: center;
    padding: 12px;
    border-radius: 12px;
    background: rgba(255,255,255,.045);
    border: 1px solid #354260;
    margin-top: 10px;
}

.action-icon {
    width: 39px;
    height: 39px;
    min-width: 39px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    background: #37396C;
    font-size: 18px;
}

.action-title {
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 800;
}

.action-description {
    color: #A4AFCA;
    font-size: 9px;
    margin-top: 4px;
}

/* Feature Cards */

.feature-card {
    background: linear-gradient(145deg, #202C49, #182139);
    border: 1px solid #374564;
    border-radius: 18px;
    padding: 22px;
    min-height: 180px;
    transition: .2s ease;
}

.feature-card:hover {
    border-color: #8175E2;
    background: linear-gradient(145deg, #293454, #202945);
    transform: translateY(-3px);
}

.feature-top {
    display: flex;
    align-items: center;
    gap: 13px;
    margin-bottom: 16px;
}

.feature-icon {
    width: 48px;
    height: 48px;
    min-width: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    font-size: 23px;
}

.feature-title {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 850;
    line-height: 1.4;
}

.feature-description {
    color: #AAB4CE;
    font-size: 11px;
    line-height: 1.8;
    min-height: 42px;
}

/* Buttons */

.stButton > button {
    background: linear-gradient(100deg, #514DAA, #675BC0);
    color: white !important;
    border: 1px solid #7971D1;
    border-radius: 10px;
    font-weight: 750;
    font-size: 11px;
    min-height: 39px;
    transition: .2s ease;
}

.stButton > button:hover {
    background: linear-gradient(100deg, #655FC5, #8072DA);
    border-color: #A49AFF;
    color: white !important;
}

/* Inputs */

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background: #1B2742 !important;
    color: white !important;
    border: 1px solid #3A4868 !important;
    border-radius: 10px !important;
}

.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: #1B2742 !important;
    border-color: #3A4868 !important;
    color: white !important;
}

[data-testid="stExpander"] {
    background: #1B2540;
    border: 1px solid #354362;
    border-radius: 12px;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid #354362;
    border-radius: 10px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #354362;
}

.stTabs [data-baseweb="tab"] {
    color: #AAB4CE;
    background: #1B2540;
    border-radius: 9px 9px 0 0;
    padding: 10px 16px;
}

.stTabs [aria-selected="true"] {
    color: #FFFFFF !important;
    background: #343568 !important;
}

.stMarkdown p {
    color: #D5DAEA;
}

hr {
    border-color: #303B59 !important;
}

.footer {
    color: #7F8BAA;
    font-size: 10px;
    text-align: center;
    border-top: 1px solid #2C3855;
    padding-top: 20px;
    margin-top: 35px;
}

@media (max-width: 900px) {
    .block-container {
        padding: 1rem !important;
    }

    .hero-title {
        font-size: 25px;
    }
}

</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.markdown(
        '<div class="brand"><span class="brand-symbol">✦</span> CampusMind <span>AI</span></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-sub">SMART LEARNING PLATFORM</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="nav-heading">YOUR WORKSPACE</div>',
        unsafe_allow_html=True
    )

    # IMPORTANT:
    # Apply pending navigation BEFORE creating the radio widget.
    # This prevents StreamlitWidgetAlreadyInstantiatedError.

    if "pending_navigation_page" in st.session_state:
        target = st.session_state.pop("pending_navigation_page")

        if target in PAGES:
            st.session_state["navigation_page"] = target

    if st.session_state.get("navigation_page") not in PAGES:
        st.session_state["navigation_page"] = "Dashboard"

    page = st.radio(
        "Navigation",
        PAGES,
        key="navigation_page",
        format_func=lambda item: f"{PAGE_ICONS[item]}   {item}",
        label_visibility="collapsed"
    )

    student_id = get_student_id()

    if student_id is not None:

        sidebar_name = html.escape(get_student_name())

        render_html(f"""
            <div class="sidebar-info">
                <div class="sidebar-info-title">👋 Hello, {sidebar_name}</div>
                <div class="sidebar-info-text">
                    Your learning workspace is ready.<br>
                    Keep learning and growing every day.
                </div>
            </div>
        """)

    else:

        render_html("""
            <div class="sidebar-info">
                <div class="sidebar-info-title">🎓 CampusMind AI</div>
                <div class="sidebar-info-text">
                    Your journey. Your skills. Your future.<br>
                    Exhibition Edition · Version 1.0
                </div>
            </div>
        """)


# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    student_id = get_student_id()
    is_logged_in = student_id is not None
    student_name = html.escape(get_student_name())

    if is_logged_in:
        try:
            stats = get_dashboard_stats(student_id)

        except Exception as error:
            st.error(f"Unable to load dashboard statistics: {error}")

            stats = {
                "assessments": 0,
                "mastered_topics": 0,
                "learning_progress": 0,
                "projects_generated": 0
            }

    else:
        stats = {
            "assessments": 0,
            "mastered_topics": 0,
            "learning_progress": 0,
            "projects_generated": 0
        }

    progress = min(100, max(0, stats["learning_progress"]))

    # TOP HEADER

    if is_logged_in:
        header_chip = f"🎓 {student_name}"
    else:
        header_chip = "✨ Welcome Guest"

    render_html(f"""
        <div class="top-header">
            <div>
                <div class="top-brand">✦ CAMPUSMIND <span>AI</span></div>
                <div class="top-caption">PERSONALIZED LEARNING & DEVELOPMENT</div>
            </div>
            <div class="profile-chip">{header_chip}</div>
        </div>
    """)

    # WELCOME HERO

    hero_left, hero_right = st.columns([1.65, 0.85], gap="medium")

    with hero_left:

        if is_logged_in:

            render_html(f"""
                <div class="hero-new">
                    <div class="hero-eyebrow">YOUR PERSONAL AI LEARNING SPACE</div>
                    <div class="hero-title">Welcome back,<br>{student_name} 👋</div>
                    <div class="hero-description">
                        Every skill you learn brings you one step closer to your goals.
                        Continue your journey with personalized AI-powered learning,
                        smart assessments and guided roadmaps.
                    </div>
                    <div class="hero-tag">✦ LEARN SMARTER · GROW FASTER</div>
                </div>
            """)

        else:

            render_html("""
                <div class="hero-new">
                    <div class="hero-eyebrow">WELCOME TO YOUR FUTURE</div>
                    <div class="hero-title">
                        CampusMind AI<br>
                        Learn Smarter. Grow Faster.
                    </div>
                    <div class="hero-description">
                        An AI-Powered Personalized Learning and Student Development
                        Platform. Discover your skills, improve your knowledge
                        and create your own learning journey with intelligent AI tools.
                    </div>
                    <div class="hero-tag">✦ YOUR JOURNEY STARTS HERE</div>
                </div>
            """)

    with hero_right:

        render_html("""
            <div class="hero-new" style="
                padding: 25px;
                background: linear-gradient(145deg, #242D58, #332D65);
                min-height: 270px;
            ">
                <div class="hero-side-icon">🚀</div>
                <div class="hero-side-title">Your Growth Journey</div>
                <div class="hero-side-text">
                    Build knowledge, discover your strengths and turn your
                    learning goals into real achievements.
                </div>
                <div class="hero-side-label">YOUR JOURNEY STARTS HERE</div>
            </div>
        """)

    # STATISTICS

    st.markdown(
        '<div class="section-heading">Your Learning Overview</div>'
        '<div class="section-description">A quick snapshot of your academic activity and achievements.</div>',
        unsafe_allow_html=True
    )

    metrics = [
        ("📈", "Learning Progress", f"{progress:.1f}%", "#344A85", "#9CB2FF"),
        ("🎯", "Skills Assessed", str(stats["assessments"]), "#285B60", "#79E2D0"),
        ("🏆", "Topics Mastered", str(stats["mastered_topics"]), "#66502F", "#FFD18B"),
        ("💡", "Projects Generated", str(stats["projects_generated"]), "#59416F", "#D5A8FF")
    ]

    cols = st.columns(4, gap="medium")

    for col, item in zip(cols, metrics):

        with col:

            render_html(f"""
                <div class="stat-card">
                    <div class="stat-icon" style="
                        background:{item[3]};
                        color:{item[4]};
                    ">
                        {item[0]}
                    </div>
                    <div class="stat-label">{item[1]}</div>
                    <div class="stat-value">{item[2]}</div>
                </div>
            """)

    # LEARNING JOURNEY

    st.markdown(
        '<div class="section-heading">Your Learning Journey</div>'
        '<div class="section-description">Monitor your roadmap and take your next learning step.</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns([1.15, 1], gap="medium")

    with left:

        render_html(f"""
            <div class="learning-panel">
                <div class="panel-top">
                    <div class="panel-title">📊 Roadmap Completion</div>
                    <div class="panel-tag">YOUR PROGRESS</div>
                </div>

                <div class="panel-description">
                    Track the activities you have completed in your saved
                    personalized learning roadmap.
                </div>

                <div class="progress-track">
                    <div class="progress-fill" style="width:{progress}%"></div>
                </div>

                <div class="progress-bottom">
                    <div class="progress-number">{progress:.1f}%</div>
                    <div class="mini-label">ACTIVITY COMPLETION</div>
                </div>
            </div>
        """)

        if st.button(
            "View Learning Progress →",
            key="open_progress",
            use_container_width=True
        ):
            open_page("Learning Progress & Topic Mastery")

    with right:

        render_html("""
            <div class="learning-panel">
                <div class="panel-top">
                    <div class="panel-title">⚡ Quick Actions</div>
                    <div class="panel-tag">GET STARTED</div>
                </div>

                <div class="action-item">
                    <div class="action-icon">🤖</div>
                    <div>
                        <div class="action-title">Ask Your AI Mentor</div>
                        <div class="action-description">Get help with difficult concepts</div>
                    </div>
                </div>

                <div class="action-item">
                    <div class="action-icon">🎯</div>
                    <div>
                        <div class="action-title">Test Your Skills</div>
                        <div class="action-description">Check your knowledge and abilities</div>
                    </div>
                </div>
            </div>
        """)

        action_left, action_right = st.columns(2)

        with action_left:
            if st.button(
                "Open AI Mentor",
                key="quick_mentor",
                use_container_width=True
            ):
                open_page("AI Personal Learning Mentor")

        with action_right:
            if st.button(
                "Take Assessment",
                key="quick_assessment",
                use_container_width=True
            ):
                open_page("Smart Skill Assessment")

    # FEATURE CARDS

    st.markdown(
        '<div class="section-heading">Explore Your Learning Tools</div>'
        '<div class="section-description">Five intelligent tools designed to support your academic and personal development.</div>',
        unsafe_allow_html=True
    )

    features = [
        {
            "icon": "🤖",
            "title": "AI Personal Learning Mentor",
            "description": "Understand difficult concepts and receive personalized AI learning guidance.",
            "page": "AI Personal Learning Mentor",
            "color": "#35417B",
            "accent": "#A7B5FF"
        },
        {
            "icon": "🎯",
            "title": "Smart Skill Assessment",
            "description": "Evaluate your knowledge, test your skills and identify areas to improve.",
            "page": "Smart Skill Assessment",
            "color": "#285B60",
            "accent": "#79E0CE"
        },
        {
            "icon": "🗺️",
            "title": "Personalized Learning Roadmap",
            "description": "Follow a structured learning plan based on your goals and skill level.",
            "page": "Personalized Learning Roadmap",
            "color": "#594477",
            "accent": "#D2ADFF"
        },
        {
            "icon": "📊",
            "title": "Learning Progress & Topic Mastery",
            "description": "Monitor your performance, completed activities and topic mastery.",
            "page": "Learning Progress & Topic Mastery",
            "color": "#66502F",
            "accent": "#FFD18B"
        },
        {
            "icon": "💡",
            "title": "AI Project Idea Generator",
            "description": "Discover project ideas that match your interests and technical skills.",
            "page": "AI Project Idea Generator",
            "color": "#694052",
            "accent": "#FFAFCB"
        }
    ]

    for start in range(0, len(features), 2):

        cols = st.columns(2, gap="medium")

        for col, feature in zip(cols, features[start:start + 2]):

            with col:

                render_html(f"""
                    <div class="feature-card">
                        <div class="feature-top">
                            <div class="feature-icon" style="
                                background:{feature['color']};
                                color:{feature['accent']};
                            ">
                                {feature['icon']}
                            </div>

                            <div class="feature-title">
                                {feature['title']}
                            </div>
                        </div>

                        <div class="feature-description">
                            {feature['description']}
                        </div>
                    </div>
                """)

                if st.button(
                    "Explore Tool →",
                    key=f"tool_{feature['page']}",
                    use_container_width=True
                ):
                    open_page(feature["page"])

    # FOOTER

    render_html("""
        <div class="footer">
            © 2026 CampusMind AI · An AI-Powered Personalized Learning and Student Development Platform
            <br><br>
            Empowering Students Through Intelligent Learning
        </div>
    """)


# ---------------- MODULE PAGES ----------------

elif page == "Student Profile":
    student_profile.render()

elif page == "AI Personal Learning Mentor":
    ai_mentor.render()

elif page == "Smart Skill Assessment":
    smart_assessment.render()

elif page == "Personalized Learning Roadmap":
    personalized_roadmap.render()

elif page == "Learning Progress & Topic Mastery":
    learning_progress.render()

elif page == "AI Project Idea Generator":
    project_idea_generator.render()
