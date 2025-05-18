import streamlit as st

# Initialize session state for quiz progress
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = {
        'current_question': 0,
        'answers': {},
        'show_results': False
    }

# Sample questions
questions = [
    {
        "id": "q1",
        "question": "What is 68 + 8?",
        "options": ["A. 88", "B. 79", "C. 76", "D. 98"],
        "correct": "C. 76",
        "difficulty": "Easy"
    },
    {
        "id": "q2",
        "question": "Which planet is known as the Red Planet?",
        "options": ["A. Earth", "B. Mars", "C. Jupiter", "D. Venus"],
        "correct": "B. Mars",
        "difficulty": "Easy"
    },
]

def display_question():
    q = questions[st.session_state.quiz_data['current_question']]
    current_q_index = st.session_state.quiz_data['current_question']
    
    st.subheader(f"Question {current_q_index + 1}/{len(questions)}")
    st.write(f"Difficulty: {q['difficulty']}")
    st.write(q["question"])
    
    # Get or initialize the selected answer for this question
    if current_q_index not in st.session_state.quiz_data['answers']:
        st.session_state.quiz_data['answers'][current_q_index] = None
    
    # Create a unique key for the radio widget
    radio_key = f"question_radio_{current_q_index}"
    
    # Display radio buttons with the currently selected answer
    selected_option = st.radio(
        "Select your answer:",
        q["options"],
        index=(
            q["options"].index(st.session_state.quiz_data['answers'][current_q_index]) 
            if st.session_state.quiz_data['answers'][current_q_index] in q["options"] 
            else None
        ),
        key=radio_key
    )
    
    # Update the selected answer in session state when changed
    if selected_option != st.session_state.quiz_data['answers'][current_q_index]:
        st.session_state.quiz_data['answers'][current_q_index] = selected_option
        st.rerun()  # Trigger a rerun to update the UI immediately

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if current_q_index > 0:
            st.button("Previous", on_click=previous_question)
    with col3:
        if current_q_index < len(questions) - 1:
            st.button("Next", on_click=next_question)
        else:
            st.button("Submit", on_click=show_results)

def next_question():
    st.session_state.quiz_data['current_question'] += 1
    st.session_state.quiz_data['show_results'] = False

def previous_question():
    st.session_state.quiz_data['current_question'] -= 1
    st.session_state.quiz_data['show_results'] = False

def show_results():
    st.session_state.quiz_data['show_results'] = True

def display_results():
    st.subheader("Quiz Results")
    correct_count = sum(
        1 for i, q in enumerate(questions) 
        if i in st.session_state.quiz_data['answers'] 
        and st.session_state.quiz_data['answers'][i] == q["correct"]
    )
    st.write(f"You scored {correct_count} out of {len(questions)}")
    
    for i, q in enumerate(questions):
        st.write(f"Question {i+1}: {q['question']}")
        if i in st.session_state.quiz_data['answers']:
            answer = st.session_state.quiz_data['answers'][i]
            if answer == q["correct"]:
                st.success(f"Your answer: {answer} (Correct)")
            else:
                st.error(f"Your answer: {answer} (Incorrect)")
                st.info(f"Correct answer: {q['correct']}")
        else:
            st.warning("You didn't answer this question")

# Quick navigation
st.write("Quick Navigation:")
cols = st.columns(min(10, len(questions)))
for i in range(min(10, len(questions))):
    with cols[i]:
        if st.button(str(i+1), disabled=i==st.session_state.quiz_data['current_question']):
            st.session_state.quiz_data['current_question'] = i
            st.session_state.quiz_data['show_results'] = False

# Main display logic
if not st.session_state.quiz_data['show_results']:
    display_question()
else:
    display_results()
    if st.button("Retake Quiz"):
        st.session_state.quiz_data = {
            'current_question': 0,
            'answers': {},
            'show_results': False
        }
        st.rerun()

# Optional debug info
st.sidebar.write("Debug Info:")
st.sidebar.write(st.session_state.quiz_data)