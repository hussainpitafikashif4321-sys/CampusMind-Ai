
import streamlit as st
import sqlite3
import hashlib
import secrets
import hmac
import html

DB_NAME = "campusmind.db"


# ---------------- DATABASE ----------------

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                semester TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL
            )
        """)


# ---------------- PASSWORD SECURITY ----------------

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200000
    )

    return hashed.hex(), salt.hex()


def verify_password(password, saved_hash, saved_salt):
    salt = bytes.fromhex(saved_salt)
    calculated_hash, _ = hash_password(password, salt)

    return hmac.compare_digest(calculated_hash, saved_hash)


# ---------------- PROFILE UI ----------------

def render():

    create_database()

    if "logged_in_user_id" not in st.session_state:
        st.session_state.logged_in_user_id = None

    user_id = st.session_state.logged_in_user_id
    profile = None

    if user_id is not None:
        with get_connection() as conn:
            profile = conn.execute("""
                SELECT full_name, email, username, department, semester
                FROM students
                WHERE id = ?
            """, (user_id,)).fetchone()

    # Profile page styling
    st.markdown("""
    <style>
    .profile-hero {
        background:
            radial-gradient(circle at 85% 15%, rgba(185,155,255,.28), transparent 30%),
            linear-gradient(115deg, #303B78, #51449A 60%, #65469A);
        border: 1px solid #625CA9;
        border-radius: 21px;
        padding: 30px;
        margin-bottom: 25px;
    }

    .profile-kicker {
        color: #D1CCFF;
        font-size: 10px;
        font-weight: 850;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }

    .profile-hero h1 {
        color: white !important;
        font-size: 29px;
        font-weight: 900;
        margin: 0 0 8px;
    }

    .profile-hero p {
        color: #E2DEFF !important;
        font-size: 12px;
        line-height: 1.8;
        margin: 0;
    }

    .profile-panel {
        background: linear-gradient(145deg, #202A47, #19223A);
        border: 1px solid #374463;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
    }

    .profile-label {
        color: #929FBE;
        font-size: 10px;
        font-weight: 750;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }

    .profile-value {
        color: #FFFFFF;
        font-size: 14px;
        font-weight: 750;
        overflow-wrap: anywhere;
    }

    .profile-welcome {
        background: linear-gradient(110deg, #292F5E, #3E3979);
        border: 1px solid #5C5AA0;
        border-radius: 15px;
        padding: 19px;
        margin-bottom: 20px;
    }

    .profile-welcome h3 {
        color: white !important;
        font-size: 19px;
        font-weight: 850;
        margin: 0 0 5px;
    }

    .profile-welcome p {
        color: #D3D2F4 !important;
        font-size: 11px;
        margin: 0;
    }

    .profile-section-title {
        color: #F5F6FF;
        font-size: 18px;
        font-weight: 850;
        margin-bottom: 5px;
    }

    .profile-section-caption {
        color: #9DA9C6;
        font-size: 11px;
        margin-bottom: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------------- PAGE HEADER ----------------

    if profile:
        display_name = html.escape(profile["full_name"])
        heading = f"Welcome back, {display_name}!"
        description = "Your student account and academic information are ready."
    else:
        heading = "Your Student Profile"
        description = (
            "Create your account, securely log in and manage your "
            "personal academic information."
        )

    st.markdown(f"""
    <div class="profile-hero">
        <div class="profile-kicker">CAMPUSMIND AI · STUDENT WORKSPACE</div>
        <h1>{heading} 👋</h1>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- TABS ----------------

    tab1, tab2, tab3 = st.tabs([
        "📝 Registration",
        "🔐 Login",
        "👤 Profile Details"
    ])

    # ---------------- REGISTRATION ----------------

    with tab1:

        st.markdown(
            '<div class="profile-section-title">Create Your Account</div>'
            '<div class="profile-section-caption">Enter your details to join the CampusMind AI learning platform.</div>',
            unsafe_allow_html=True
        )

        with st.form("registration_form"):

            col1, col2 = st.columns(2)

            with col1:
                full_name = st.text_input("Full Name", placeholder="Enter your full name")
                email = st.text_input("Email Address", placeholder="example@email.com")
                username = st.text_input("Username", placeholder="Choose a username")

            with col2:
                department = st.selectbox(
                    "Department",
                    [
                        "Select Department",
                        "Computer Science",
                        "Information Technology",
                        "Software Engineering",
                        "Education",
                        "Other"
                    ]
                )

                semester = st.selectbox(
                    "Current Semester",
                    [
                        "Select Semester",
                        "1st Semester",
                        "2nd Semester",
                        "3rd Semester",
                        "4th Semester",
                        "5th Semester",
                        "6th Semester",
                        "7th Semester",
                        "8th Semester"
                    ]
                )

            st.divider()

            col3, col4 = st.columns(2)

            with col3:
                password = st.text_input(
                    "Create Password",
                    type="password",
                    placeholder="Minimum 8 characters"
                )

            with col4:
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Enter password again"
                )

            agree = st.checkbox(
                "I confirm that the information provided above is correct."
            )

            submitted = st.form_submit_button(
                "Create Student Account →",
                use_container_width=True
            )

            if submitted:

                if not all([
                    full_name.strip(),
                    email.strip(),
                    username.strip(),
                    password,
                    confirm_password
                ]):
                    st.error("Please fill in all required fields.")

                elif (
                    "@" not in email
                    or "." not in email.split("@")[-1]
                ):
                    st.error("Please enter a valid email address.")

                elif department == "Select Department":
                    st.error("Please select your department.")

                elif semester == "Select Semester":
                    st.error("Please select your semester.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                elif len(password) < 8:
                    st.error("Password must contain at least 8 characters.")

                elif not agree:
                    st.error("Please confirm your information.")

                else:
                    password_hash, password_salt = hash_password(password)

                    try:
                        with get_connection() as conn:
                            conn.execute("""
                                INSERT INTO students (
                                    full_name,
                                    email,
                                    username,
                                    department,
                                    semester,
                                    password_hash,
                                    password_salt
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                full_name.strip(),
                                email.strip().lower(),
                                username.strip(),
                                department,
                                semester,
                                password_hash,
                                password_salt
                            ))

                        st.success(
                            "Registration successful! Your account has been saved. "
                            "You can now log in."
                        )

                    except sqlite3.IntegrityError:
                        st.error(
                            "This email or username is already registered."
                        )

    # ---------------- LOGIN ----------------

    with tab2:

        st.markdown(
            '<div class="profile-section-title">Welcome Back</div>'
            '<div class="profile-section-caption">Log in to continue your personalized learning journey.</div>',
            unsafe_allow_html=True
        )

        if st.session_state.logged_in_user_id is not None:

            st.success("You are already logged in.")

            if profile:
                st.markdown(
                    f"**Logged in as:** {html.escape(profile['full_name'])}"
                )

        else:

            with st.form("login_form"):

                login_email = st.text_input(
                    "Email Address",
                    placeholder="Enter your registered email"
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )

                login_button = st.form_submit_button(
                    "Login to CampusMind AI →",
                    use_container_width=True
                )

                if login_button:

                    if not login_email or not login_password:
                        st.error("Please enter your email and password.")

                    else:
                        with get_connection() as conn:
                            student = conn.execute("""
                                SELECT *
                                FROM students
                                WHERE email = ?
                            """, (
                                login_email.strip().lower(),
                            )).fetchone()

                        if student and verify_password(
                            login_password,
                            student["password_hash"],
                            student["password_salt"]
                        ):

                            st.session_state.logged_in_user_id = student["id"]
                            st.session_state.student_name = student["full_name"]

                            st.success("Login successful!")
                            st.rerun()

                        else:
                            st.error("Invalid email or password.")

    # ---------------- PROFILE DETAILS ----------------

    with tab3:

        st.markdown(
            '<div class="profile-section-title">Your Academic Profile</div>'
            '<div class="profile-section-caption">View your saved personal and academic information.</div>',
            unsafe_allow_html=True
        )

        user_id = st.session_state.logged_in_user_id

        if user_id is not None:

            with get_connection() as conn:
                profile = conn.execute("""
                    SELECT full_name, email, username,
                           department, semester
                    FROM students
                    WHERE id = ?
                """, (user_id,)).fetchone()

            if profile:

                display_name = html.escape(profile["full_name"])

                st.markdown(f"""
                <div class="profile-welcome">
                    <h3>👋 Hello, {display_name}</h3>
                    <p>Your CampusMind AI student account is active.</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                fields = [
                    ("FULL NAME", profile["full_name"], "👤"),
                    ("EMAIL ADDRESS", profile["email"], "✉️"),
                    ("USERNAME", profile["username"], "♙"),
                    ("DEPARTMENT", profile["department"], "🎓"),
                    ("CURRENT SEMESTER", profile["semester"], "📚")
                ]

                for index, (label, value, icon) in enumerate(fields):
                    target_col = col1 if index % 2 == 0 else col2

                    with target_col:
                        safe_value = html.escape(str(value))
                        st.markdown(f"""
                        <div class="profile-panel">
                            <div class="profile-label">{icon} {label}</div>
                            <div class="profile-value">{safe_value}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.divider()

                if st.button(
                    "🚪 Logout",
                    use_container_width=True
                ):
                    st.session_state.logged_in_user_id = None
                    st.session_state.pop("student_name", None)
                    st.session_state.pop("logged_in_user_name", None)

                    st.success("You have logged out successfully.")
                    st.rerun()

            else:
                st.error("Student record not found.")
                st.session_state.logged_in_user_id = None
                st.session_state.pop("student_name", None)

        else:
            st.info(
                "Please log in first to view your personal profile details."
            )

    st.markdown("""
    <div style="
        text-align:center;
        color:#7F8BAA;
        font-size:10px;
        border-top:1px solid #2C3855;
        padding-top:18px;
        margin-top:28px;
    ">
        © 2026 CampusMind AI · Student Development Workspace
    </div>
    """, unsafe_allow_html=True)
