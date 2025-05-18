import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase (do this only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_math_questions():
    # Reference to the Math document's subcollection
    questions_ref = db.collection("Questions").document("Math").collections()
    
    all_questions = []
    
    for collection in questions_ref:
        for doc in collection.stream():
            question_data = doc.to_dict()
            question_data['id'] = doc.id  # Include document ID in the data
            all_questions.append(question_data)
    
    return all_questions

def search_question_by_Box_id(question_id):
    # Search across all subcollections under Math
    collections = db.collection("Questions").document("Math").collections()
    
    for collection in collections:
        doc_ref = collection.document(question_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    return None

def search_question_by_BoxALL_id(DIC_ID):
    # Handle both single ID and list of IDs
    if isinstance(DIC_ID, list):
        results = {}
        for id in DIC_ID:
            if isinstance(id, str):  # Only process string IDs
                doc_ref = db.collection("Questions").document("Math").collection("All").document(id)
                doc = doc_ref.get()
                if doc.exists:
                    results[id] = doc.to_dict()
        return results if results else None
    else:
        # Single ID case
        doc_ref = db.collection("Questions").document("Math").collection("All").document(DIC_ID)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None


# Search by ID section
st.subheader("Search by Question ID")
question_id = st.text_input("Enter Question ID:")

if st.button("Search"): 
    if question_id:
        question = search_question_by_Box_id(question_id)
        if question:
            st.success("Question Found!")
            
            # Display the QuestionIDs
            if "QuestionIDs" in question:
                st.write("Question IDs:")
                st.write(question["QuestionIDs"])  # Display as-is first
                
                # Handle the QuestionIDs (could be string or list)
                DIC_ID = question["QuestionIDs"]
                question_IDS = search_question_by_BoxALL_id(DIC_ID)
                
                if question_IDS:
                    st.success("Found matching documents in All collection:")
                    if isinstance(question_IDS, dict):
                        # Display each found document
                        for doc_id, doc_data in question_IDS.items():
                            st.subheader(f"Document ID: {doc_id}")
                            
                            st.table(doc_data)
                    else:
                        # Single document case
                        st.dataframe(question_IDS)
                else:
                    st.warning("No documents found in All collection with those IDs")
            else:
                st.warning("No QuestionIDs field found in the document")
        else:
            st.warning("No question found with that ID")
    else:
        st.warning("Please enter a Question ID")