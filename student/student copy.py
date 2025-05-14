import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
import random
import time
from typing import Dict, List, Tuple, Optional

# Constants
SUBJECTS = ["Math", "Science", "Physics", "Chemistry", "Biology"]
TEST_TYPES = ["All"]

# Initialize Firestore connection with caching
@st.cache_resource
def get_db():
    """Cached Firestore connection"""
    return st.session_state.db

# Topic management with caching
@st.cache_data(ttl=3600)
def get_topics(subject: str) -> Dict[str, str]:
    """Fetch available topics for a subject"""
    topics_ref = db.collection("ScienceTopics").document(subject)
    topics_doc = topics_ref.get()
    return {k: v for k, v in topics_doc.to_dict().items() 
            if k.startswith("TID") and v} if topics_doc.exists else {}

@st.cache_data(ttl=300)
def get_questions(subject: str, test_type: str, topic_filter: list = None) -> List[Dict]:
    """Get questions with optional topic filtering"""
    questions_ref = db.collection("Questions").document(subject).collection(test_type)
    
    if topic_filter:
        questions = questions_ref.where("Topics", "array_contains_any", topic_filter).stream()
    else:
        questions = questions_ref.stream()
    
    return [doc.to_dict() for doc in questions]

def display_question(question: Dict, question_num: int, total_questions: int) -> str:
    """Display a question and return the selected answer"""
    with st.container(border=True):
        st.markdown(f"### Question {question_num}/{total_questions}")
        st.markdown(f"**{question['question']}**")
        
        # Display images if available
        if "Image" in question and question["Image"]:
            display_images(question["Image"])
        
        # Display options
        options = ["A", "B", "C", "D"]
        selected = st.radio(
            "Select your answer:",
            options,
            format_func=lambda x: f"{x}. {question[x]}",
            key=f"q_{question_num}"
        )
        
        return selected

def display_images(image_urls: List[str], cols: int = 3) -> None:
    """Display images in columns"""
    st.markdown("**Reference Images:**")
    columns = st.columns(min(cols, len(image_urls)))
    for idx, img in enumerate(image_urls[:cols]):
        with columns[idx % cols]:
            try:
                st.image(img, width=150)
            except:
                st.markdown(f"📎 [Image Link]({img})")

def calculate_score(answers: List[str], questions: List[Dict]) -> Tuple[int, List[Dict]]:
    """Calculate test score and return results"""
    score = 0
    results = []
    
    for idx, (answer, question) in enumerate(zip(answers, questions)):
        is_correct = answer == question["answer"]
        if is_correct:
            score += 1
        
        results.append({
            "question": question["question"],
            "your_answer": f"{answer}. {question[answer]}",
            "correct_answer": f"{question['answer']}. {question[question['answer']]}",
            "is_correct": is_correct,
            "question_images": question.get("Image", []),
            "question_number": idx + 1
        })
    
    return score, results

def show_results(score: int, total: int, results: List[Dict]) -> None:
    """Display test results with detailed feedback"""
    percentage = (score / total) * 100
    
    st.title("📝 Test Results")
    st.subheader(f"Score: {score}/{total} ({percentage:.1f}%)")
    
    if percentage >= 80:
        st.success("🎉 Excellent work! You've mastered this material.")
    elif percentage >= 60:
        st.warning("👍 Good effort! Review your mistakes to improve.")
    else:
        st.error("📚 Keep practicing! Focus on the topics you missed.")
    
    with st.expander("📖 View Detailed Results", expanded=False):
        for result in results:
            with st.container(border=True):
                st.markdown(f"### Question {result['question_number']}")
                st.markdown(f"**{result['question']}**")
                
                if result["question_images"]:
                    display_images(result["question_images"], cols=2)
                
                if result["is_correct"]:
                    st.success(f"✅ Your answer: {result['your_answer']}")
                else:
                    st.error(f"❌ Your answer: {result['your_answer']}")
                    st.info(f"Correct answer: {result['correct_answer']}")

def take_test(subject: str, test_type: str, topic_filter: list = None, num_questions: int = 10) -> None:
    """Main test-taking function"""
    questions = get_questions(subject, test_type, topic_filter)
    
    if not questions:
        st.error("No questions found for the selected criteria.")
        return
    
    # Randomly select questions if there are more than requested
    if len(questions) > num_questions:
        questions = random.sample(questions, num_questions)
    else:
        num_questions = len(questions)
        st.info(f"Only {num_questions} questions available for this selection.")
    
    # Initialize session state for test
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.answers = [None] * num_questions
        st.session_state.test_started = True
        st.session_state.test_submitted = False
    
    # Display progress bar
    progress = st.progress((st.session_state.current_question) / num_questions)
    
    # Display current question or results
    if not st.session_state.test_submitted:
        if st.session_state.current_question < num_questions:
            # Show current question
            selected = display_question(
                questions[st.session_state.current_question],
                st.session_state.current_question + 1,
                num_questions
            )
            
            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.session_state.current_question > 0 and st.button("⬅️ Previous"):
                    st.session_state.current_question -= 1
                    st.rerun()
            
            with col2:
                if st.button("🏁 Submit Test" if st.session_state.current_question == num_questions - 1 else "Next ➡️"):
                    st.session_state.answers[st.session_state.current_question] = selected
                    
                    if st.session_state.current_question == num_questions - 1:
                        st.session_state.test_submitted = True
                        st.session_state.results = calculate_score(st.session_state.answers, questions)
                        st.rerun()
                    else:
                        st.session_state.current_question += 1
                        st.rerun()
            
            # Store answer when moving forward
            st.session_state.answers[st.session_state.current_question] = selected
        else:
            st.session_state.test_submitted = True
            st.session_state.results = calculate_score(st.session_state.answers, questions)
            st.rerun()
    else:
        # Show results
        show_results(st.session_state.results[0], num_questions, st.session_state.results[1])
        
        if st.button("🔄 Take Another Test"):
            reset_test_session()
            st.rerun()

def reset_test_session() -> None:
    """Reset test session state"""
    keys = ['current_question', 'answers', 'test_started', 'test_submitted', 'results']
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def test_selection_form() -> Tuple[str, str, list, int]:
    """Form for selecting test parameters"""
    st.title("📚 Student Exam Portal")
    
    with st.form("test_selection"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Select Subject", SUBJECTS)
        with col2:
            test_type = st.selectbox("Select Test Type", TEST_TYPES)
        
        # Topic selection (optional)
        topics = get_topics(subject)
        selected_topics = st.multiselect(
            "Filter by Topics (optional)",
            options=list(topics.values()),
            help="Select specific topics or leave blank for all topics"
        )
        topic_ids = [k for k, v in topics.items() if v in selected_topics]
        
        # Number of questions
        num_questions = st.slider(
            "Number of Questions",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
        
        if st.form_submit_button("Start Test"):
            return subject, test_type, topic_ids, num_questions
    
    return None, None, None, None

def main() -> None:
    """Main application function"""
    # Initialize session state if not exists
    if 'test_started' not in st.session_state:
        st.session_state.test_started = False
    
    if not st.session_state.test_started:
        # Show test selection form
        subject, test_type, topic_ids, num_questions = test_selection_form()
        if subject and test_type:
            st.session_state.test_params = {
                "subject": subject,
                "test_type": test_type,
                "topic_ids": topic_ids,
                "num_questions": num_questions
            }
            st.session_state.test_started = True
            st.rerun()
    else:
        # Start or continue the test
        params = st.session_state.test_params
        take_test(
            params["subject"],
            params["test_type"],
            params["topic_ids"],
            params["num_questions"]
        )

if __name__ == "__main__":
    db = get_db()
    main()