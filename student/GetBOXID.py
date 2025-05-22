import streamlit as st

# Initialize session state

# Database reference
db = st.session_state.db


def search_question_by_box_id(Box_ID):
    """Search for a question by ID across all Math collections"""
    collections = db.collection("Questions").document("Math").collections()
    
    for collection in collections:
        doc_ref = collection.document(Box_ID)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
    
    return None

def display_quiz_results():
   
def display_quiz_form():
   

def BoxId():
    """Main application function"""
    st.title("Math Quiz App")
    
    # Search functionality
    st.subheader("Search by Box ID")
    Box_ID = st.text_input("Enter Box ID")
    
    if st.button("Search"):
        if not Box_ID:
            st.warning("Please enter a Box ID")
            return
        
        question = search_question_by_box_id(Box_ID)
        
        if not question:
            st.warning("No question found with that ID")
            return
        
        st.success("Question Found!")
        
        if "QuestionIDs" not in question:
            st.warning("No QuestionIDs field found in the document")
            return
        
    
        
        st.session_state['submitted'] = False
        display_quiz_form(questions)


if __name__ == "BoxId":
    BoxId()