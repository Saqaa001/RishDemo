import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Constants
SUBJECTS = ["Math", "Science", "Physics", "Chemistry", "Biology"]
TEST_TYPES = ["All", "Practice", "Exam", "Quiz"]

def initialize_session_state():
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = {
            'current_question': 0,
            'answers': {},
            'show_results': False,
            'subject': None,
            'test_type': None,
            'topic_filter': None,
            'questions_loaded': False,
            'percentage': 0,
            'test_started': False,
            'unanswered_questions': [],
            'show_setup_form': True,
            'show_stats': False,
            'test_history': []
        }
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'test_params' not in st.session_state:
        st.session_state.test_params = {}
    if 'test_start_time' not in st.session_state:
        st.session_state.test_start_time = time.time()
    if 'review_incorrect' not in st.session_state:
        st.session_state.review_incorrect = False

def reset_quiz_state():
    st.session_state.quiz_data = {
        'current_question': 0,
        'answers': {},
        'show_results': False,
        'subject': None,
        'test_type': None,
        'topic_filter': None,
        'questions_loaded': False,
        'percentage': 0,
        'test_started': False,
        'unanswered_questions': [],
        'show_setup_form': True,
        'show_stats': False,
        'test_history': st.session_state.quiz_data.get('test_history', [])
    }
    st.session_state.questions = []
    st.rerun()


@st.cache_data(ttl=3600)
def get_topics(subject: str) -> Dict[str, Dict]:
    try:
        topics_ref = st.session_state.db.collection("ScienceTopics").document(subject)
        topics_doc = topics_ref.get()
        if not topics_doc.exists:
            return {}
        topics_data = topics_doc.to_dict()
        return {
            k: v for k, v in topics_data.items()
            if k.startswith("TID") and isinstance(v, dict) and "name" in v
        }
    except Exception as e:
        st.error(f"Error loading topics: {str(e)}")
        return {}


@st.cache_data(ttl=300)
def get_questions(subject: str, test_type: str, topic_filter: Optional[List[str]] = None) -> List[Dict]:
    try:
        questions_ref = st.session_state.db.collection("Questions").document(subject).collection(test_type)
        if topic_filter:
            questions = questions_ref.where("Topics", "array_contains_any", topic_filter).stream()
        else:
            questions = questions_ref.stream()
        questions_list = []
        for doc in questions:
            if doc.exists:
                data = doc.to_dict()
                options = [f"{opt}. {data[opt]}" for opt in ['A', 'B', 'C', 'D'] if opt in data]
                question = {
                    "id": doc.id,
                    "question": data.get("question", ""),
                    "options": options,
                    "correct": f"{data.get('answer', '')}. {data.get(data.get('answer', ''), '')}",
                    "difficulty": data.get("Question_Deficulity", "Unknown"),
                    "topics": data.get("Topics", []),
                    "science_type": data.get("science_type", ""),
                    "test_type": data.get("test_type", ""),
                    "created_at": data.get("created_at", ""),
                    "image": data.get("Image", []),
                    "success_rate": data.get("success_rate", 0),
                    "usage_count": data.get("usage_count", 0),
                    "QID": doc.id,
                    "explanation": data.get("explanation", "No explanation available.")
                }
                questions_list.append(question)
        return questions_list
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return []


def save_test_result_to_firestore(user_id: str, answers: Dict[int, str], questions: List[Dict], threshold: int, start_time: float):
    end_time = time.time()
    duration = int(end_time - start_time)
    datenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    answers_map = {}
    for idx, question in enumerate(questions):
        qid = question.get("QID")
        if not qid:
            continue

        selected_option = answers.get(idx, "W")
        if selected_option and selected_option.strip():
            cleaned_option = selected_option[0].upper()
            if cleaned_option in ("A", "B", "C", "D"):
                answers_map[qid] = cleaned_option
            else:
                answers_map[qid] = "Unanswered"
        else:
            answers_map[qid] = "Unanswered"

    test_result = {
        "Threshold": st.session_state.Threshold,
        "duration": duration,
        "timestamp": datenow,
        "answers": answers_map,
        "percentage": st.session_state.quiz_data['percentage'],
        "subject": st.session_state.quiz_data['subject'],
        "topics": st.session_state.quiz_data['topic_filter'],
        "test_type": st.session_state.quiz_data['test_type']
    }

    try:
        student_ref = st.session_state.db.collection("Student").document(user_id)
        test_collection = student_ref.collection("By-student_generated_test")
        doc_ref = test_collection.document()
        test_result["BoxID"] = doc_ref.id
        doc_ref.set(test_result)
        st.success("✅ Test results saved to your profile.")
    except Exception as e:
        st.error(f"🔥 Failed to save results: {e}")


def next_question():
    st.session_state.quiz_data['current_question'] += 1
    st.session_state.quiz_data['show_results'] = False
    st.rerun()


def previous_question():
    st.session_state.quiz_data['current_question'] -= 1
    st.session_state.quiz_data['show_results'] = False
    st.rerun()


def show_results():
    unanswered = [
        i for i in range(len(st.session_state.questions))
        if i not in st.session_state.quiz_data['answers']
        or st.session_state.quiz_data['answers'][i] is None
    ]
    st.session_state.quiz_data['unanswered_questions'] = unanswered
    
    if unanswered:
        st.warning(f"You haven't answered {len(unanswered)} questions!")
    
    st.session_state.quiz_data['show_results'] = True
    st.rerun()


def display_quick_navigation(questions: List[Dict]):
    if not questions:
        return
    
    st.write("Quick Navigation:")
    max_buttons_per_row = 10
    total_questions = len(questions)
    total_rows = (total_questions + max_buttons_per_row - 1) // max_buttons_per_row
    
    for row in range(total_rows):
        start_idx = row * max_buttons_per_row
        end_idx = min((row + 1) * max_buttons_per_row, total_questions)
        cols = st.columns(end_idx - start_idx)
        
        for i in range(start_idx, end_idx):
            with cols[i - start_idx]:
                current_q = st.session_state.quiz_data['current_question']
                answered = i in st.session_state.quiz_data['answers'] and st.session_state.quiz_data['answers'][i] is not None
                correct = answered and st.session_state.quiz_data['answers'][i] == questions[i].get("correct")
                unanswered = i in st.session_state.quiz_data.get('unanswered_questions', [])
                
                button_label = str(i+1)
                
                if i == current_q:
                    button_type = "primary"
                    button_color = "violet"
                elif correct:
                    button_type = "secondary"
                    button_color = "green"
                elif answered:
                    button_type = "secondary"
                    button_color = "red"
                elif unanswered:
                    button_type = "secondary"
                    button_color = "orange"
                else:
                    button_type = "secondary"
                    button_color = "gray"
                
                if unanswered:
                    button_label = f"⚠️{button_label}"
                
                colored_label = f":{button_color}[{button_label}]"
                
                if st.button(
                    colored_label,
                    type=button_type,
                    disabled=i == current_q,
                    key=f"nav_{i}"
                ):
                    st.session_state.quiz_data['current_question'] = i
                    st.session_state.quiz_data['show_results'] = False
                    st.rerun()


def display_question(questions: List[Dict]):
    if not questions:
        st.warning("No questions available for the selected criteria.")
        return

    q = questions[st.session_state.quiz_data['current_question']]
    current_q_index = st.session_state.quiz_data['current_question']

    st.subheader(f"Question {current_q_index + 1}/{len(questions)}")
    difficulty = int(q.get("difficulty", 1))
    st.write(f"Difficulty: {'⭐' * difficulty}{'☆' * (5 - difficulty)}")
    st.write(q["question"])
    if q.get("image"):
        for img_url in q["image"]:
            st.image(img_url)

    answer_key = f"answer_{current_q_index}"
    if answer_key not in st.session_state:
        st.session_state[answer_key] = st.session_state.quiz_data['answers'].get(current_q_index)

    def update_answer():
        st.session_state.quiz_data['answers'][current_q_index] = st.session_state[answer_key]
        if current_q_index in st.session_state.quiz_data.get('unanswered_questions', []):
            st.session_state.quiz_data['unanswered_questions'].remove(current_q_index)

    st.radio(
        "Select your answer:",
        q.get("options", []),
        key=answer_key,
        on_change=update_answer,
        index=None if current_q_index not in st.session_state.quiz_data['answers'] else None
    )

    col1, col2, col3 = st.columns([2, 6, 2])
    with col1:
        if current_q_index > 0:
            if st.button("⏮ Previous"):
                previous_question()
    with col3:
        if current_q_index < len(questions) - 1:
            if st.button("Next ⏭"):
                next_question()
        else:
            if st.button("Submit ✅"):
                show_results()


def display_results(questions: List[Dict]):
    if not questions:
        return

    st.subheader("Quiz Results")

    correct_count = sum(
        1 for i, q in enumerate(questions)
        if i in st.session_state.quiz_data['answers']
        and st.session_state.quiz_data['answers'][i] == q.get("correct")
    )
    unanswered_count = len(st.session_state.quiz_data.get('unanswered_questions', []))
    score_percentage = (correct_count / len(questions)) * 100
    st.session_state.quiz_data['percentage'] = score_percentage

    # Add to test history
    test_result = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'subject': st.session_state.quiz_data['subject'],
        'test_type': st.session_state.quiz_data['test_type'],
        'score': score_percentage,
        'correct': correct_count,
        'total': len(questions),
        'topics': st.session_state.quiz_data['topic_filter']
    }
    st.session_state.quiz_data['test_history'].append(test_result)

    st.write(f"You scored {correct_count} out of {len(questions)} ({score_percentage:.1f}%)")
    st.progress(score_percentage / 100)

    if unanswered_count > 0:
        st.error(f"⚠️ You didn't answer {unanswered_count} questions:")
        unanswered_list = ", ".join([str(i+1) for i in st.session_state.quiz_data['unanswered_questions']])
        st.write(unanswered_list)

    if score_percentage >= 80:
        st.success("Excellent performance! 🎉")
    elif score_percentage >= 60:
        st.info("Good job! Keep practicing 👍")
    else:
        st.warning("Keep working at it! You'll improve with practice 💪")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔍 Review Incorrect"):
            st.session_state.review_incorrect = True
            st.rerun()
    with col2:
        if st.session_state.get('user_id'):
            if st.button("💾 Save Results"):
                save_test_result_to_firestore(
                    st.session_state.user_id,
                    st.session_state.quiz_data['answers'],
                    st.session_state.questions,
                    0,
                    st.session_state.test_start_time
                )
    with col3:
        if st.button("📊 View Stats"):
            st.session_state.quiz_data['show_stats'] = True
            st.rerun()
    with col4:
        if st.button("🔄 New Quiz"):
            reset_quiz_state()


def display_incorrect_answers():
    if 'quiz_data' not in st.session_state or not st.session_state.quiz_data.get('show_results'):
        st.error("No test results to review.")
        if st.button("Return to Test"):
            st.session_state.review_incorrect = False
            st.rerun()
        return
    
    questions = st.session_state.questions
    answers = st.session_state.quiz_data['answers']
    
    incorrect_answers = []
    for i, q in enumerate(questions):
        is_correct = i in answers and answers[i] == q.get("correct")
        if not is_correct:
            incorrect_answers.append({
                'question_number': i + 1,
                'question': q["question"],
                'question_images': q.get("image", []),
                'your_answer': answers.get(i, "Unanswered"),
                'correct_answer': q.get("correct", ""),
                'Topics': q.get("Topics", []),
                'explanation': q.get("explanation", "No explanation available.")
            })
    
    if not incorrect_answers:
        st.success("🎉 You didn't get any questions wrong!")
        if st.button("Return to Test"):
            st.session_state.review_incorrect = False
            st.rerun()
        return
    
    st.title("📝 Review Incorrect Answers")
    st.markdown(f"**You got {len(incorrect_answers)} questions wrong. Let's review them:**")
    
    for result in incorrect_answers:
        with st.container(border=True):
            st.markdown(f"### Question {result['question_number']}")
            st.markdown(f"**{result['question']}**")
            
            if result["question_images"]:
                for img_url in result["question_images"]:
                    st.image(img_url)
            
            col1, col2 = st.columns(2)
            with col1:
                st.error(f"**Your answer:** {result['your_answer']}")
            with col2:
                st.success(f"**Correct answer:** {result['correct_answer']}")
            
            if 'topics' in st.session_state:
                Question_topic = result['Topics']
                science_topic = st.session_state.topics
                result_topics = {key: science_topic[key] for key in Question_topic if key in science_topic}
                for key, value in result_topics.items():
                    st.link_button(f"📚 Learn about {value['name']}", value.get("url", "#"))
            
            if result["explanation"]:
                with st.expander("🔍 Explanation", expanded=True):
                    st.markdown(result["explanation"])
    
    if st.button("✅ I've Reviewed These Questions", type="primary"):
        st.session_state.review_incorrect = False
        st.rerun()


def show_quiz_setup():
    with st.form("quiz_setup"):
        st.subheader("Quiz Setup")
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Select Subject", SUBJECTS, key="setup_subject")
        with col2:
            test_type = st.selectbox("Select Test Type", TEST_TYPES, key="setup_test_type")
        
        st.slider("Target Score (%)", 50, 100, 80, 5, 
                 help="Set your target passing percentage", 
                 key="setup_threshold")
        
        topics = get_topics(subject)
        if topics:
            topic_options = [f"{tid}: {details['name']}" for tid, details in topics.items()]
            selected_topics = st.multiselect("Filter by Topics (optional)", topic_options, key="setup_topics")
            topic_filter = [t.split(":")[0] for t in selected_topics] if selected_topics else None
        else:
            topic_filter = None
            st.info("No topics available for this subject")

        submitted = st.form_submit_button("Start Quiz")
        
        if submitted:
            st.session_state.Threshold = st.session_state.setup_threshold
            initialize_quiz(subject, test_type, topic_filter)
            st.session_state.quiz_data['show_setup_form'] = False
            st.rerun()


def initialize_quiz(subject: str, test_type: str, topic_filter: Optional[List[str]] = None):
    st.session_state.quiz_data = {
        'current_question': 0,
        'answers': {},
        'show_results': False,
        'subject': subject,
        'test_type': test_type,
        'topic_filter': topic_filter,
        'questions_loaded': True,
        'percentage': 0,
        'test_started': True,
        'unanswered_questions': [],
        'show_setup_form': False,
        'show_stats': False,
        'test_history': st.session_state.quiz_data.get('test_history', [])
    }
    st.session_state.questions = get_questions(subject, test_type, topic_filter)
    st.session_state.test_start_time = time.time()

def show_statistics():
    st.title("📊 Your Quiz Statistics")
    
    if not st.session_state.quiz_data.get('test_history'):
        st.warning("No test history available. Complete some quizzes to see statistics.")
        if st.button("Back to Quiz"):
            st.session_state.quiz_data['show_stats'] = False
            st.rerun()
        return
    
    # Convert test history to DataFrame
    history_df = pd.DataFrame(st.session_state.quiz_data['test_history'])
    
    # Overall performance metrics
    st.subheader("Overall Performance")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tests Taken", len(history_df))
    with col2:
        avg_score = history_df['score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    with col3:
        best_score = history_df['score'].max()
        st.metric("Best Score", f"{best_score:.1f}%")
    
    # Score distribution chart
    st.subheader("Score Distribution")
    fig = px.histogram(history_df, x='score', nbins=10, 
                       title="Distribution of Your Scores",
                       labels={'score': 'Score (%)'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Best Idea section
    st.subheader("🌟 Best Idea")
    st.write("Here's your best performing area based on your quiz history:")
    
    # Find the subject with highest average score (minimum 3 attempts)
    subject_stats = history_df.groupby('subject')['score'].agg(['mean', 'count'])
    subject_stats = subject_stats[subject_stats['count'] >= 3]  # Only consider subjects with at least 3 attempts
    
    if not subject_stats.empty:
        best_subject = subject_stats['mean'].idxmax()
        best_subject_score = subject_stats['mean'].max()
        st.success(f"Your strongest subject is **{best_subject}** with an average score of **{best_subject_score:.1f}%**")
        
        # Display some motivational tips based on performance
        if best_subject_score >= 90:
            st.write("🎯 You're excelling in this area! Consider challenging yourself with advanced materials.")
        elif best_subject_score >= 75:
            st.write("👍 You're doing well! Focus on your weaker areas to maintain this strength while improving others.")
        else:
            st.write("💡 You have potential here! With more practice, you could turn this into a real strength.")
    else:
        st.info("Complete at least 3 quizzes in a subject to identify your best performing area.")
    
    # Subject performance breakdown
    if len(history_df['subject'].unique()) > 1:
        st.subheader("Performance by Subject")
        subject_stats = history_df.groupby('subject')['score'].agg(['mean', 'count'])
        subject_stats = subject_stats.rename(columns={'mean': 'Average Score', 'count': 'Tests Taken'})
        st.dataframe(subject_stats.style.format({'Average Score': '{:.1f}%'}))
    
    # Test type performance breakdown
    if len(history_df['test_type'].unique()) > 1:
        st.subheader("Performance by Test Type")
        test_type_stats = history_df.groupby('test_type')['score'].agg(['mean', 'count'])
        test_type_stats = test_type_stats.rename(columns={'mean': 'Average Score', 'count': 'Tests Taken'})
        st.dataframe(test_type_stats.style.format({'Average Score': '{:.1f}%'}))
    
    if st.button("Back to Quiz"):
        st.session_state.quiz_data['show_stats'] = False
        st.rerun()

def show_quiz_interface():
    questions = st.session_state.questions
    if not questions:
        st.warning("No questions found for the selected criteria.")
        if st.button("Back to Setup"):
            reset_quiz_state()
        return
    
    if st.session_state.get('review_incorrect'):
        display_incorrect_answers()
        return
    
    if st.session_state.quiz_data.get('show_stats'):
        show_statistics()
        return
    
    if st.button("⚙️ Change Quiz Settings"):
        st.session_state.quiz_data['show_setup_form'] = True
        st.rerun()
    
    st.subheader(f"{st.session_state.quiz_data['subject']} - {st.session_state.quiz_data['test_type']}")
    if st.session_state.quiz_data['topic_filter']:
        topics = get_topics(st.session_state.quiz_data['subject'])
        topic_names = [topics[tid]['name'] for tid in st.session_state.quiz_data['topic_filter'] if tid in topics]
        st.caption(f"Topics: {', '.join(topic_names)}")
    
    display_quick_navigation(questions)
    
    if not st.session_state.quiz_data['show_results']:
        display_question(questions)
    else:
        display_results(questions)


def main():
    st.title("Science Quiz App")
    initialize_session_state()
    
    if st.session_state.quiz_data.get('show_setup_form') or not st.session_state.quiz_data.get('questions_loaded'):
        show_quiz_setup()
    else:
        show_quiz_interface()

if __name__ == "__main__":
    main()