import sqlite3

DB_NAME = "campusmind.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_progress_tables():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessment_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                selected_topic TEXT,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessment_question_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                topic TEXT NOT NULL,
                question_text TEXT NOT NULL,
                student_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                explanation TEXT,
                FOREIGN KEY (attempt_id)
                    REFERENCES assessment_attempts(id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS roadmap_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                goal TEXT NOT NULL,
                subject TEXT NOT NULL,
                level TEXT NOT NULL,
                daily_time INTEGER NOT NULL,
                duration_weeks INTEGER NOT NULL,
                roadmap_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS roadmap_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roadmap_id INTEGER NOT NULL,
                week_number INTEGER NOT NULL,
                day_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                completed_at TEXT,
                FOREIGN KEY (roadmap_id)
                    REFERENCES roadmap_records(id)
                    ON DELETE CASCADE
            )
        """)

        # Project idea generation history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_idea_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                interests TEXT,
                idea_count INTEGER NOT NULL,
                generated_ideas TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessment_student
            ON assessment_attempts(student_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_roadmap_student
            ON roadmap_records(student_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_roadmap_topics
            ON roadmap_topics(roadmap_id, status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_history_student
            ON project_idea_history(student_id)
        """)


def save_project_idea_history(
    student_id,
    subject,
    level,
    category,
    interests,
    idea_count,
    generated_ideas
):

    create_progress_tables()

    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO project_idea_history (
                student_id,
                subject,
                level,
                category,
                interests,
                idea_count,
                generated_ideas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            subject,
            level,
            category,
            interests,
            idea_count,
            generated_ideas
        ))

        conn.commit()

    finally:
        conn.close()


def get_project_idea_history(student_id, limit=20):

    create_progress_tables()

    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM project_idea_history
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (student_id, limit)).fetchall()

    finally:
        conn.close()