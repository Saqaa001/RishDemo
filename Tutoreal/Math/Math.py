import streamlit as st

# Page title
st.title("📘 Welcome to the Tutorial Page")
st.subheader("Learn how to use the Educational Portal")

# Sidebar info
st.sidebar.success("Use this page to learn how to navigate the app.")

# Tabs for sections
tabs = st.tabs(["🧭 Overview", "👨‍🏫 For Students", "🧑‍🏫 For Teachers", "📺 Video Tutorial"])

# --- Overview Tab ---
with tabs[0]:
    st.markdown("""
    ### 🎯 What is this App?
    This is a web-based educational platform that allows:
    - Students to take quizzes
    - Teachers to create/manage questions
    - View performance statistics

    ### 🔐 Roles:
    - **Student**: Can register, log in, and take quizzes.
    - **Teacher**: Can manage questions, quizzes, and review results.

    ---  
    """)

# --- Students Tab ---
with tabs[1]:
    st.markdown("""
    ### 👨‍🎓 How to Use for Students
    1. Go to the **Login** page and sign in as a student.
    2. Choose a subject (e.g., Math, Science).
    3. Take available quizzes.
    4. Review your scores under **Statistics**.

    ✅ You will see a timer for each quiz.
    """)

# --- Teachers Tab ---
with tabs[2]:
    st.markdown("""
    ### 👩‍🏫 How to Use for Teachers
    1. Log in with a **teacher account**.
    2. Go to **Manage Questions** to:
       - Add/edit/delete questions
       - Upload images (if needed)
    3. View student results under **Statistics**.

    📤 You can also upload bulk questions via CSV (coming soon).
    """)

# --- Video Tutorial Tab ---
with tabs[3]:
    st.markdown("### 🎥 Watch a Quick Walkthrough")
    st.video("https://www.youtube.com/watch?v=Vx2ffIYDRk8")  # replace with your own video link

    st.info("If the video doesn’t load, check your internet connection or open it directly on YouTube.")

