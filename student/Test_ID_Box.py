import streamlit as st
from typing import List, Dict, Union, Optional
from datetime import datetime

# Initialize Firestore DB
db = st.session_state.db

# Initialize session state for quiz progress
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = {
        'current_question': 0,
        'answers': {},
        'show_results': False,
        'questions': [],
        'quiz_loaded': False,
        'time_spent': {},  # Track time spent per question
        'bookmarked': set(),  # Track bookmarked questions
        'start_time': None  # Track when quiz was started
    }

# Database functions (unchanged)
def search_question_by_box_id(question_id: str) -> Optional[Dict]:
    collections = db.collection("Questions").document("Math").collections()
    for collection in collections:
        doc = collection.document(question_id).get()
        if doc.exists:
            return doc.to_dict()
    return None

def search_question_by_box_all_id(box_ids: Union[str, List[str]]) -> Union[Optional[Dict], Dict]:
    all_collection = db.collection("Questions").document("Math").collection("All")
    if isinstance(box_ids, list):
        return {box_id: all_collection.document(box_id).get().to_dict() 
                for box_id in box_ids if all_collection.document(box_id).get().exists}
    doc = all_collection.document(box_ids).get()
    return doc.to_dict() if doc.exists else None

def load_quiz_questions(question_set_id: str) -> bool:
    st.session_state.serBox = question_set_id
    try:
        question_set = search_question_by_box_id(question_set_id)
        if not question_set or "QuestionIDs" not in question_set:
            st.error("Question set not found or invalid format")
            return False

        question_ids = question_set["QuestionIDs"]
        
        questions_data = search_question_by_box_all_id(question_ids)

        if not questions_data:
            st.error("No questions found for the provided IDs")
            return False

        formatted_questions = []
        for doc_id, data in questions_data.items():
            options_dict = {
                "A": data.get("A", ""),
                "B": data.get("B", ""),
                "C": data.get("C", ""),
                "D": data.get("D", "")
            }

            correct_opt = data.get("answer", "")
            correct_text = options_dict.get(correct_opt, "")
            correct_answer = f"{correct_opt}. {correct_text}"

            question = {
                "id": doc_id,
                "question": data.get("question", ""),
                "options": options_dict,
                "correct": correct_opt,
                "correct_text": correct_text,
                "correct_answer_full": correct_answer,
                "difficulty": data.get("Question_Deficulity", "Unknown"),
                "topics": data.get("Topics", []),
                "science_type": data.get("science_type", ""),
                "test_type": data.get("test_type", ""),
                "created_at": data.get("created_at", ""),
                "image": data.get("Image", []),
                "success_rate": data.get("success_rate", 0),
                "usage_count": data.get("usage_count", 0),
                "QID": doc_id,
                "explanation": data.get("explanation", "No explanation available.")
            }

            formatted_questions.append(question)

        st.session_state.quiz_data = {
            'current_question': 0,
            'answers': {},
            'show_results': False,
            'questions': formatted_questions,
            'quiz_loaded': True,
            'time_spent': {},
            'bookmarked': set(),
            'start_time': datetime.now().timestamp()  # Record start time when loading quiz
        }
        return True
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return False

def save_test_result_to_firestore(user_id: str, answers: Dict[int, str], questions: List[Dict], threshold: int, start_time: float):
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
                answers_map[qid] = "W"
        else:
            answers_map[qid] = "W"

    test_result = {
        "answers": answers_map,
        "timestamp": datenow,
        "duration_seconds": int(datetime.now().timestamp() - start_time),
        "total_questions": len(questions)
    }

    try:
        student_ref = db.collection("Student").document(user_id)
        test_collection = student_ref.collection("Box_test")
        doc_ref = test_collection.document()
        test_result["BoxID"] = st.session_state.serBox
        doc_ref.set(test_result)
        st.success("✅ Test results saved to your profile.")

        doc_idd = test_result["BoxID"]  
        
        docId = "Box"
        
        student_id = st.session_state.user_id


        taken_test = doc_ref

       
        doc_ref = db.collection("Student_path_test_by_box").document(doc_idd)
        existing_data = doc_ref.get().to_dict() or {}

    
        if docId in existing_data:
            if student_id in existing_data[docId]:
  
                existing_data[docId][student_id].append(taken_test)
            else:
 
                existing_data[docId][student_id] = [taken_test]
        else:
       
            existing_data = {
                docId: {
                    student_id: [taken_test]
                }
            }

        # Set/update the document
        doc_ref.set(existing_data)
        return True





    except Exception as e:
        st.error(f"🔥 Failed to save results: {e}")

def calculate_score(answers: Dict[int, str], questions: List[Dict]) -> int:
    correct = 0
    for i, q in enumerate(questions):
        user_answer = answers.get(i)
        if user_answer and user_answer.startswith(q["correct"]):
            correct += 1
    return correct

def display_question():
    if not st.session_state.quiz_data.get('questions'):
        st.warning("No questions loaded. Please load a quiz first.")
        return
    
    current_idx = st.session_state.quiz_data['current_question']
    question = st.session_state.quiz_data['questions'][current_idx]
    
    # Question header with navigation and bookmark
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        st.subheader(f"Question {current_idx + 1}/{len(st.session_state.quiz_data['questions'])}")
    with col3:
        bookmark_key = f"bookmark_{current_idx}"
        is_bookmarked = current_idx in st.session_state.quiz_data['bookmarked']
        if st.button("⭐" if is_bookmarked else "☆", key=bookmark_key):
            if is_bookmarked:
                st.session_state.quiz_data['bookmarked'].remove(current_idx)
            else:
                st.session_state.quiz_data['bookmarked'].add(current_idx)
            st.rerun()
    
    # Question content with better formatting
    with st.container(border=True):
        st.markdown(f"**Difficulty:** {question['difficulty']}")
        st.markdown(f"**Question:** {question['question']}")
        
        # Display image if exists
        if question.get('image'):
            st.image(question['image'], use_column_width=True)
        
        # Initialize answer if not exists
        if current_idx not in st.session_state.quiz_data['answers']:
            st.session_state.quiz_data['answers'][current_idx] = None
        
        # Create clean options list
        options = [
            f"A. {question['options']['A']}",
            f"B. {question['options']['B']}",
            f"C. {question['options']['C']}",
            f"D. {question['options']['D']}"
        ]
        
        # Get current answer if exists
        current_answer = st.session_state.quiz_data['answers'].get(current_idx)
        
        # Display clean radio buttons
        selected_option = st.radio(
            "Select your answer:",
            options=options,
            index=options.index(current_answer) if current_answer in options else None,
            key=f"question_{current_idx}"
        )
        
        # Update answer if changed
        if selected_option != current_answer:
            st.session_state.quiz_data['answers'][current_idx] = selected_option
            st.rerun()
    
    # Navigation buttons
    nav_cols = st.columns([1, 1, 1, 1, 1])
    with nav_cols[0]:
        if st.button("◀ Previous", disabled=current_idx == 0):
            previous_question()
    with nav_cols[4]:
        if current_idx < len(st.session_state.quiz_data['questions']) - 1:
            if st.button("Next ▶"):
                next_question()
        else:
            if st.button("Submit Quiz", type="primary"):
                st.balloons()
                show_results()

def next_question():
    st.session_state.quiz_data['current_question'] += 1
    st.session_state.quiz_data['show_results'] = False
    st.rerun()

def previous_question():
    st.session_state.quiz_data['current_question'] -= 1
    st.session_state.quiz_data['show_results'] = False
    st.rerun()

def show_results():
    st.session_state.quiz_data['show_results'] = True
    # Save results to Firestore when showing results
    if st.session_state.get('user_id'):    
        save_test_result_to_firestore(
            st.session_state.user_id,
            st.session_state.quiz_data['answers'],
            st.session_state.quiz_data['questions'],
            0,
            st.session_state.quiz_data['start_time']
        )
    st.rerun()

# def display_results():
    # questions = st.session_state.quiz_data['questions']
    # answers = st.session_state.quiz_data['answers']
  
    
    # st.subheader("Quiz Results")
  
    # for i, q in enumerate(questions):
    #     user_answer = answers.get(i)
    #     is_correct = user_answer and user_answer.startswith(q["correct"])
        
        # with st.expander(f"Question {i+1}: {'✅' if is_correct else '❌'}"):
        #     st.markdown(f"**Question:** {q['question']}")
        #     st.markdown(f"**Your answer:** {user_answer if user_answer else 'Unanswered'}")
        #     st.markdown(f"**Correct answer:** {q['correct_answer_full']}")
        #     st.markdown(f"**Explanation:** {q['explanation']}")

def display_quick_navigation():
    st.write("**Jump to Question:**")
    questions = st.session_state.quiz_data['questions']
    cols_per_row = 8
    rows = (len(questions) + cols_per_row - 1) // cols_per_row
    
    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            q_idx = row * cols_per_row + col_idx
            if q_idx >= len(questions):
                break
            
            with cols[col_idx]:
                is_current = q_idx == st.session_state.quiz_data['current_question']
                is_answered = q_idx in st.session_state.quiz_data['answers']
                is_bookmarked = q_idx in st.session_state.quiz_data['bookmarked']
                
                btn_label = f"{'⭐' if is_bookmarked else ''}{q_idx+1}"
                btn_type = "primary" if is_current else ("secondary" if is_answered else "secondary")
                
                if st.button(btn_label, key=f"nav_{q_idx}", disabled=is_current, type=btn_type):
                    st.session_state.quiz_data['current_question'] = q_idx
                    st.session_state.quiz_data['show_results'] = False
                    st.rerun()

# Sidebar controls
with st.sidebar:
    st.header("Quiz Controls")
    question_set_id = st.text_input("Enter Question Set ID:")
    if st.button("Load Quiz", type="primary"):
        if question_set_id:
            with st.spinner("Loading questions..."):
                if load_quiz_questions(question_set_id):
                    st.success("Quiz loaded!")
        else:
            st.warning("Please enter a question set ID")
    
    if st.button("Reset Quiz"):
        st.session_state.quiz_data = {
            'current_question': 0,
            'answers': {},
            'show_results': False,
            'questions': [],
            'quiz_loaded': False,
            'time_spent': {},
            'bookmarked': set(),
            'start_time': None
        }
        st.success("Quiz reset!")
        st.rerun()
    
    if st.session_state.quiz_data.get('quiz_loaded'):
        st.divider()
        st.markdown("**Bookmarked Questions**")
        bookmarked = sorted(st.session_state.quiz_data['bookmarked'])
        if not bookmarked:
            st.info("No bookmarked questions")
        else:
            for q_idx in bookmarked:
                if st.button(f"Question {q_idx + 1}", key=f"bm_{q_idx}"):
                    st.session_state.quiz_data['current_question'] = q_idx
                    st.session_state.quiz_data['show_results'] = False
                    st.rerun()

# Main app display
if st.session_state.quiz_data.get('quiz_loaded'):
    if not st.session_state.quiz_data['show_results']:
        display_quick_navigation()
        display_question()
    # else:
    #     display_results()
else:
    st.info("Please load a quiz using the sidebar controls")