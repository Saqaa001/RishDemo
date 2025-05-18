import streamlit as st

subject_data   = ["Math", "Science", "History", "English"]
test_type_data = ["All", "Practice", "Mock", "Final"]
topic_data     = ["", "Algebra", "Geometry", "Trigonometry", "Calculus"]

# Main form

with st.container():
    st.write("")
    col1, col2 = st.columns(2)

    with col1:
        subject = st.selectbox("Select Subject", subject_data)

    with col2:
        test_type = st.selectbox("Select Test Type", test_type_data)

    st.markdown("###", unsafe_allow_html=True)

    topic = st.selectbox("Filter by Topics (optional)",topic_data)

    selected_questions = st.slider("Number of Questions", min_value=5, max_value=50, value=10)

    st.markdown("###", unsafe_allow_html=True)

    if st.button("Start Test"):
        st.success(f"Starting {test_type} test in {subject} with {selected_questions} questions on topic '{topic or 'All Topics'}'")

    