import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase (do this only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_math_questions():
    questions_ref = db.collection("Questions").document("Math").collections()
    all_questions = []
    for collection in questions_ref:
        for doc in collection.stream():
            question_data = doc.to_dict()
            question_data['id'] = doc.id
            all_questions.append(question_data)
    return all_questions

def search_question_by_Box_id(question_id):
    collections = db.collection("Questions").document("Math").collections()
    for collection in collections:
        doc_ref = collection.document(question_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    return None

def search_question_by_BoxALL_id(DIC_ID):
    if isinstance(DIC_ID, list):
        results = {}
        for id in DIC_ID:
            if isinstance(id, str):
                doc_ref = db.collection("Questions").document("Math").collection("All").document(id)
                doc = doc_ref.get()
                if doc.exists:
                    results[id] = doc.to_dict()
        return results if results else None
    else:
        doc_ref = db.collection("Questions").document("Math").collection("All").document(DIC_ID)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None

def display_quiz_form(questions):
    """Display a quiz form with checkbox or radio button options"""
    st.subheader("Quiz Time!")
    st.write("Please answer the following questions:")
    
    student_answers = {}
    score = 0
    total_questions = len(questions)
    
    if isinstance(questions, dict):
        for q_id, question_data in questions.items():
            with st.expander(f"Question {q_id}"):
                st.write(question_data.get('question', 'No question text available'))
                
                # Check if question has options
                if 'options' in question_data:
                    options = question_data['options']
                    
                    # Determine if multiple answers are allowed
                    multiple_correct = question_data.get('multiple_correct', False)
                    
                    if multiple_correct:
                        # Use checkboxes for multiple correct answers
                        st.write("Select all that apply:")
                        selected_options = []
                        for i, option in enumerate(options):
                            if st.checkbox(option, key=f"q_{q_id}_opt_{i}"):
                                selected_options.append(option)
                        student_answers[q_id] = selected_options
                        
                        # Check if all correct answers are selected and no incorrect ones
                        correct_answers = question_data.get('answer', [])
                        if set(selected_options) == set(correct_answers):
                            score += 1
                    else:
                        # Use radio buttons for single correct answer
                        answer = st.radio(
                            "Select the correct answer:",
                            options,
                            key=f"q_{q_id}"
                        )
                        student_answers[q_id] = answer
                        
                        # Check if answer is correct
                        if 'answer' in question_data and answer == question_data['answer']:
                            score += 1
                else:
                    # Fallback to text input if no options provided
                    answer = st.text_area(
                        "Your answer:",
                        key=f"q_{q_id}"
                    )
                    student_answers[q_id] = answer
    else:
        # Handle single question case
        q_id = list(questions.keys())[0] if isinstance(questions, dict) else "1"
        question_data = questions if not isinstance(questions, dict) else questions[q_id]
        
        st.write(question_data.get('question', 'No question text available'))
        
        if 'options' in question_data:
            options = question_data['options']
            multiple_correct = question_data.get('multiple_correct', False)
            
            if multiple_correct:
                st.write("Select all that apply:")
                selected_options = []
                for i, option in enumerate(options):
                    if st.checkbox(option, key=f"q_{q_id}_opt_{i}"):
                        selected_options.append(option)
                student_answers[q_id] = selected_options
                
                correct_answers = question_data.get('answer', [])
                if set(selected_options) == set(correct_answers):
                    score = 1
            else:
                answer = st.radio(
                    "Select the correct answer:",
                    options,
                    key=f"q_{q_id}"
                )
                student_answers[q_id] = answer
                
                if 'answer' in question_data and answer == question_data['answer']:
                    score = 1
        else:
            answer = st.text_area(
                "Your answer:",
                key=f"q_{q_id}"
            )
            student_answers[q_id] = answer
    
    if st.button("Submit Quiz"):
        st.session_state['submitted'] = True
        st.session_state['score'] = score
        st.session_state['total'] = total_questions
        st.session_state['answers'] = student_answers
    
    if st.session_state.get('submitted', False):
        st.success(f"Quiz submitted! Your score: {st.session_state['score']}/{st.session_state['total']}")
        
        st.subheader("Review Your Answers:")
        questions_to_review = questions if isinstance(questions, dict) else {q_id: questions}
        
        for q_id, question_data in questions_to_review.items():
            with st.expander(f"Question {q_id}", expanded=False):
                st.write(f"**Question:** {question_data.get('question', 'No question text')}")
                
                user_answer = st.session_state['answers'].get(q_id, 'No answer')
                if isinstance(user_answer, list):
                    st.write(f"**Your answers:** {', '.join(user_answer) if user_answer else 'None selected'}")
                else:
                    st.write(f"**Your answer:** {user_answer}")
                
                if 'answer' in question_data:
                    correct_answer = question_data['answer']
                    if isinstance(correct_answer, list):
                        st.write(f"**Correct answers:** {', '.join(correct_answer)}")
                    else:
                        st.write(f"**Correct answer:** {correct_answer}")
                
                if 'explanation' in question_data:
                    st.write(f"**Explanation:** {question_data['explanation']}")

# Initialize session state
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

# Main app
st.title("Math Quiz App")
st.subheader("Search by Question ID")
question_id = st.text_input("Enter Question ID:")

if st.button("Search"): 
    if question_id:
        question = search_question_by_Box_id(question_id)
        if question:
            st.success("Question Found!")
            
            if "QuestionIDs" in question:
                DIC_ID = question["QuestionIDs"]
                question_IDS = search_question_by_BoxALL_id(DIC_ID)
                
                if question_IDS:
                    st.success("Found matching documents in All collection:")
                    st.session_state['submitted'] = False
                    
                    if isinstance(question_IDS, dict):
                        display_quiz_form(question_IDS)
                    else:
                        display_quiz_form({question_id: question_IDS})
                else:
                    st.warning("No documents found in All collection with those IDs")
            else:
                st.warning("No QuestionIDs field found in the document")
        else:
            st.warning("No question found with that ID")
    else:
        st.warning("Please enter a Question ID")