import streamlit as st

# Assuming db is initialized elsewhere and available in session_state
db = st.session_state.db

def get_student_username(student_id):
    """Retrieve username from Student collection"""
    student_ref = db.collection("Student").document(student_id)
    doc = student_ref.get()
    return doc.to_dict().get("username", "Unknown") if doc.exists else "Unknown"


def get_student_taken_test(ref):

    taken_test = {}
    doc = ref.get()

    # Print the result
    if doc.exists:
        taken_test = doc.to_dict()

    else:
        print("Document not found.")

    return taken_test 




def get_question_body(question_id):
    doc_ref = db.collection("Questions").document("Math").collection("All").document(question_id)
    question_body = doc_ref.get().to_dict()
    return question_body



def main():
    st.title("Field Viewer by ID")
    
    # Initialize session state
    if 'selected_box' not in st.session_state:
        st.session_state.selected_box = None
    if 'box_data' not in st.session_state:
        st.session_state.box_data = {}
    
    # Search section
    st.header("Search Field by ID")
    field_id = st.text_input("Enter Field ID:", "L0AkesFie8dxqXEXfOAZ")
    
    if st.button("Search"):
        doc_ref = db.collection("Student_path_test_by_box").document(field_id)
        doc = doc_ref.get()
        
        if doc.exists:
            st.session_state.box_data = doc.to_dict().get("Box", {})
            if st.session_state.box_data and not st.session_state.selected_box:
                st.session_state.selected_box = next(iter(st.session_state.box_data.keys()))
    
    # Display results if data exists
    if st.session_state.box_data:
        st.write(f"### Viewing Field: {field_id}")
        st.write("---")
        
        # Create two columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.session_state.selected_box:
                st.subheader(f"Documents in Box: {get_student_username(st.session_state.selected_box)}")
                doc_refs = st.session_state.box_data[st.session_state.selected_box]
                
                if isinstance(doc_refs, list):
                    st.write(f"**Total documents:** {len(doc_refs)}")
                    for i, doc_ref in enumerate(doc_refs, 1):
                        taken_test = get_student_taken_test(doc_ref)
                        answers = taken_test.get("answers")
                        for qid,answer  in answers.items():

                            st.write(answer)
                            question_body = get_question_body(qid)
                            st.write(question_body)
                            if answer == question_body.get("answer"):
                                st.write("ok")
                            else:
                                st.write("no")
                else:
                    st.write("doc_refs")
        
        with col2:
            st.subheader("Available Boxes")
            st.write(f"**Total boxes:** {len(st.session_state.box_data)}")
            
            if st.session_state.selected_box:
                doc_refs = st.session_state.box_data[st.session_state.selected_box]
                count = len(doc_refs) if isinstance(doc_refs, list) else 1
                st.write(f"**Current box documents:** {count}")
            
            st.write("### Select Box:")
            for box_id in st.session_state.box_data:
                username = get_student_username(box_id)
                if st.button(username, key=f"btn_{box_id}"):
                    st.session_state.selected_box = box_id
                    st.rerun()

if __name__ == "__main__":
    main()





