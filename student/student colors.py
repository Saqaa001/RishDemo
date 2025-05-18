import streamlit as st
import json

# Initialize session state for quiz progress
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = {
        'current_question': 0,
        'answers': {},
        'show_results': False
    }

# Function to save session state to URL
def save_session_state():
    state = {
        'current_question': st.session_state.quiz_data['current_question'],
        'answers': st.session_state.quiz_data['answers'],
        'show_results': st.session_state.quiz_data['show_results']
    }
    st.query_params['quiz_state'] = json.dumps(state)

# Function to load session state from URL
def load_session_state():
    if 'quiz_state' in st.query_params:
        try:
            state = json.loads(st.query_params['quiz_state'])
            st.session_state.quiz_data = {
                'current_question': state['current_question'],
                'answers': {int(k): v for k, v in state['answers'].items()},
                'show_results': state['show_results']
            }
        except:
            pass

# Load saved state when page loads
load_session_state()

# Sample questions (truncated for brevity - include all your questions here)
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
    }
    # Add all your remaining questions...
]

def display_question():
    q = questions[st.session_state.quiz_data['current_question']]
    current_q_index = st.session_state.quiz_data['current_question']
    
    st.subheader(f"Question {current_q_index + 1}/{len(questions)}")
    st.write(f"Difficulty: {q['difficulty']}")
    st.write(q["question"])
    
    if current_q_index not in st.session_state.quiz_data['answers']:
        st.session_state.quiz_data['answers'][current_q_index] = None
    
    radio_key = f"question_radio_{current_q_index}"
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
    
    if selected_option != st.session_state.quiz_data['answers'][current_q_index]:
        st.session_state.quiz_data['answers'][current_q_index] = selected_option
        save_session_state()
        st.rerun()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if current_q_index > 0 and st.button("Previous"):
            previous_question()
    with col3:
        if current_q_index < len(questions) - 1 and st.button("Next"):
            next_question()
        elif st.button("Submit"):
            show_results()

def next_question():
    st.session_state.quiz_data['current_question'] += 1
    st.session_state.quiz_data['show_results'] = False
    save_session_state()
    st.rerun()

def previous_question():
    st.session_state.quiz_data['current_question'] -= 1
    st.session_state.quiz_data['show_results'] = False
    save_session_state()
    st.rerun()

def show_results():
    st.session_state.quiz_data['show_results'] = True
    save_session_state()
    st.rerun()

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

# Quick Navigation with Dynamic Answer-Based Coloring
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
            
            if i == current_q:
                label = f":violet[{i+1}]"
                btn_type = "primary"
            elif answered:
                label = f":green[{i+1}]"
                btn_type = "secondary"
            else:
                label = f":red[{i+1}]"
                btn_type = "secondary"
            
            if st.button(
                label,
                type=btn_type,
                disabled=i == current_q,
                key=f"nav_{i}"
            ):
                st.session_state.quiz_data['current_question'] = i
                st.session_state.quiz_data['show_results'] = False
                save_session_state()
                st.rerun()



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
        save_session_state()
        st.rerun()

# Debug info
st.sidebar.write("Debug Info:")
st.sidebar.write("Session State:", st.session_state.quiz_data)
st.sidebar.write("Query Params:", dict(st.query_params))