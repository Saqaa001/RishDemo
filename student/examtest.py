import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import time

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    .question-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .timer {
        font-size: 1.5rem;
        color: #d9534f;
        font-weight: bold;
    }
    .header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


# Initialize session state variables
if 'exam_started' not in st.session_state:
    st.session_state.exam_started = False
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'time_remaining' not in st.session_state:
    st.session_state.time_remaining = timedelta(minutes=30)
if 'exam_submitted' not in st.session_state:
    st.session_state.exam_submitted = False

# Sample exam questions
exam_questions = []

def start_exam():
    st.session_state.exam_started = True
    st.session_state.start_time = datetime.now()
    st.session_state.end_time = st.session_state.start_time + st.session_state.time_remaining

def submit_exam():
    st.session_state.exam_submitted = True
    calculate_score()

def calculate_score():
    total_points = sum(q["points"] for q in exam_questions)
    earned_points = 0
    
    for question in exam_questions:
        q_id = str(question["id"])
        if q_id in st.session_state.answers:
            if question["type"] in ["multiple_choice", "true_false"]:
                if st.session_state.answers[q_id] == question["correct_answer"]:
                    earned_points += question["points"]
            elif question["type"] == "short_answer":
                if st.session_state.answers[q_id].lower().strip() == question["correct_answer"].lower().strip():
                    earned_points += question["points"]
    
    st.session_state.score = (earned_points / total_points) * 100

def display_timer():
    if st.session_state.exam_started and not st.session_state.exam_submitted:
        now = datetime.now()
        if now < st.session_state.end_time:
            remaining = st.session_state.end_time - now
            st.session_state.time_remaining = remaining
        else:
            st.session_state.time_remaining = timedelta(0)
            submit_exam()
        
        # Display timer
        minutes, seconds = divmod(st.session_state.time_remaining.seconds, 60)
        st.sidebar.markdown(f"<div class='timer'>Time Remaining: {minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)
        
        # Update every second
        time.sleep(1)
        st.rerun()  # Changed from st.experimental_rerun() to st.rerun()

# Main app
def main():
    st.title("📝 School Exam System")
    
    if not st.session_state.exam_started and not st.session_state.exam_submitted:
        st.markdown("<div class='header'>Exam Instructions</div>", unsafe_allow_html=True)
        st.write(""" """)
        
        TestBox_Id = st.text_input("TestBox_Id")
       
        if st.button("Start Exam"):
            if TestBox_Id :
                start_exam()
            else:
                st.warning("Please enter your TestBox_Id and name before starting the exam.")
    
    elif st.session_state.exam_submitted:
        st.markdown("<div class='header'>Exam Submitted</div>", unsafe_allow_html=True)
        st.success("Thank you for completing the exam!")
        st.write(f"Your score: {st.session_state.score:.1f}%")
        
        # Show correct answers (for demonstration)
        st.subheader("Correct Answers:")
        for question in exam_questions:
            if question["type"] != "essay":
                st.write(f"Question {question['id']}: {question.get('correct_answer', 'N/A')}")
    
    else:
        display_timer()
        
        st.markdown("<div class='header'>Exam Questions</div>", unsafe_allow_html=True)
        
        for question in exam_questions:
            display_question(question)
        
        if st.button("Submit Exam", on_click=submit_exam):
            pass

if __name__ == "__main__":
    main()