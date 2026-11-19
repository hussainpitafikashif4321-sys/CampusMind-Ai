
import streamlit as st
import json
import urllib.request
import urllib.error

MODEL_NAME = "qwen2.5:1.5b"
OLLAMA_URL = "http://localhost:11434/api/chat"


def stream_ai_response(messages):
    system_message = {
        "role": "system",
        "content": (
            "You are CampusMind AI, a friendly and helpful Personal "
            "Learning Mentor for university students. "
            "Explain concepts in easy English. "
            "Give clear definitions, simple examples and step-by-step "
            "guidance. Help students with programming, university "
            "subjects, assignments, study planning and academic growth. "
            "Keep answers understandable and well organized."
        )
    }

    chat_messages = [system_message]

    for message in messages:
        chat_messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    payload = {
        "model": MODEL_NAME,
        "messages": chat_messages,
        "stream": True,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.5
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        for line in response:
            if not line.strip():
                continue

            data = json.loads(line.decode("utf-8"))
            content = data.get("message", {}).get("content", "")

            if content:
                yield content


def render():
    st.markdown("""
    <div style="
        background:linear-gradient(120deg,#5145C8,#7751D7,#A05BCB);
        padding:28px;
        border-radius:18px;
        margin-bottom:25px;
    ">
        <h1 style="color:white;margin:0;">
            🤖 AI Personal Learning Mentor
        </h1>
        <p style="color:#EEE9FF;margin-top:8px;">
            Your personal AI guide for learning, studying and academic growth.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "mentor_messages" not in st.session_state:
        st.session_state.mentor_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! 👋 Welcome to your Personal Learning Mentor. "
                    "Ask me about your subjects, programming, study plans "
                    "or academic concepts."
                )
            }
        ]

    st.subheader("💬 Learning Conversation")
    st.caption("Ask questions and get personalized learning guidance.")

    for message in st.session_state.mentor_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_question = st.chat_input(
        "Ask your learning question here..."
    )

    if user_question:
        st.session_state.mentor_messages.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.write(user_question)

        with st.chat_message("assistant"):
            try:
                with st.spinner("🧠 CampusMind AI is starting..."):
                    ai_reply = st.write_stream(
                        stream_ai_response(
                            st.session_state.mentor_messages
                        )
                    )

                st.session_state.mentor_messages.append({
                    "role": "assistant",
                    "content": ai_reply
                })

            except urllib.error.URLError:
                error_message = (
                    "⚠️ I cannot connect to Ollama right now. "
                    "Please make sure Ollama is running."
                )
                st.error(error_message)

                st.session_state.mentor_messages.append({
                    "role": "assistant",
                    "content": error_message
                })

            except Exception as error:
                error_message = (
                    "⚠️ Something went wrong while generating "
                    "the response. Error: " + str(error)
                )
                st.error(error_message)

                st.session_state.mentor_messages.append({
                    "role": "assistant",
                    "content": error_message
                })

    st.divider()

    st.markdown("""
    <div style="
        background:rgba(81,69,200,0.15);
        border:1px solid rgba(150,120,255,0.35);
        padding:18px;
        border-radius:14px;
    ">
        <h4 style="color:#C9B8FF;margin-top:0;">
            🧠 AI Mentor Engine
        </h4>
        <p style="color:#DDD8F5;margin-bottom:0;">
            Powered by Qwen2.5:1.5b through Ollama.
            Running locally on your computer.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat History"):
        st.session_state.mentor_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! 👋 Welcome to your Personal Learning Mentor. "
                    "How can I help you with your learning?"
                )
            }
        ]
        st.rerun()
