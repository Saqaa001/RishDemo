# student.py - Student test-taking interface
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from PIL import Image
import requests
from io import BytesIO

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(".streamlit/firebase.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def display_question(question_data, question_number):
    st.subheader(f"Question {question_number}")
    st.write(question_data["Question"])
    
    if "Image" in question_data and question_data["Image"]:
        try:
            response = requests.get(question_data["Image"][0])
            img = Image.open(BytesIO(response.content))
            st.image(img, caption="Question Image", use_column_width=True)
        except:
            st.warning("Couldn't load question image")
    
    options = [question_data.get("A", ""), question_data.get("B", ""), 
               question_data.get("C", ""), question_data.get("D", "")]
    options = [opt for opt in options if opt]
    
    user_answer = st.radio("Select your answer:", options, key=f"q{question_number}")
    return user_answer

def main():
    st.title("Mathematics Test")
    
    # Student information (could be expanded with proper authentication)
    student_name = st.text_input("Enter your name")
    if not student_name:
        st.warning("Please enter your name to continue")
        return
    
    test_type = st.selectbox("Select Test", ["M1Test", "J1Test"])
    
    questions_ref = db.collection("Questions").document("Math").collection(test_type)
    questions = [doc.to_dict() for doc in questions_ref.stream()]
    
    if not questions:
        st.warning("No questions found for this test.")
        return
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    
    for i, question in enumerate(questions, 1):
        user_answer = display_question(question, i)
        st.session_state.answers[f"q{i}"] = user_answer
    
    if st.button("Submit Test") and not st.session_state.submitted:
        st.session_state.submitted = True
        score = 0
        
        for i, question in enumerate(questions, 1):
            correct_answer_key = question["answer"]
            correct_answer = question.get(correct_answer_key, "")
            user_answer = st.session_state.answers.get(f"q{i}", "")
            
            if user_answer == correct_answer:
                score += 1
        
        # Store student results (you could add this to Firebase)
        st.success(f"Test submitted, {student_name}! Your score: {score}/{len(questions)}")
        
        st.subheader("Correct Answers")
        for i, question in enumerate(questions, 1):
            correct_answer_key = question["answer"]
            correct_answer = question.get(correct_answer_key, "")
            user_answer = st.session_state.answers.get(f"q{i}", "")
            
            st.write(f"Question {i}: Correct answer is {correct_answer_key} ({correct_answer})")
            st.write(f"Your answer: {user_answer}")
            st.write("---")

if __name__ == "__main__":
    main()