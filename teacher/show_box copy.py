import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# Initialize Firebase
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase initialization error: {str(e)}")
        st.stop()

db = init_firebase()

# Data operations functions
@st.cache_data(ttl=300)
def get_box_names() -> list:
    """Get all question boxes"""
    try:
        collections = db.collection("Questions").document("Math").collections()
        return sorted([col.id for col in collections if col.id != "All"])
    except Exception as e:
        st.error(f"Error loading boxes: {str(e)}")
        return []

def fetch_box_data(box_name: str) -> dict:
    """Get data from a box (without caching for editing purposes)"""
    try:
        docs = db.collection("Questions").document("Math").collection(box_name).stream()
        return {
            doc.id: {
                "QuestionIDs": doc.to_dict().get("QuestionIDs", []),
                "WhichGroup": doc.to_dict().get("WhichGroup", "Not specified"),
                "ref": doc.reference  # Save document reference for updates
            } for doc in docs
        }
    except Exception as e:
        st.error(f"Error loading box {box_name}: {str(e)}")
        return {}

@st.cache_data(ttl=60)
def batch_get_questions(q_ids: list) -> dict:
    """Batch load questions"""
    try:
        all_ref = db.collection("Questions").document("Math").collection("All")
        return {q_id: doc.to_dict() for q_id in q_ids 
                if (doc := all_ref.document(q_id).get()).exists}
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return {}

def update_group(doc_ref, new_group: str):
    """Update group for a document"""
    try:
        doc_ref.update({"WhichGroup": new_group})
        st.success("Group updated successfully!")
        st.cache_data.clear()  # Clear cache for fresh data
    except Exception as e:
        st.error(f"Update error: {str(e)}")

# UI Components
def render_group_editor(doc_id: str, current_group: str, doc_ref):
    """UI for group editing"""
    with st.form(key=f"edit_{doc_id}"):
        new_group = st.text_input(
            "New group", 
            value=current_group,
            key=f"input_{doc_id}"
        )
        if st.form_submit_button("💾 Save"):
            update_group(doc_ref, new_group)
            return True
    return False

def Show_box():
    st.title("🧮 Question Management with Groups")
    
    # Data loading
    box_names = get_box_names()
    selected_box = st.sidebar.selectbox(
        "📦 Select box", 
        box_names,
        help="Select a box to work with questions"
    )
    
    if not selected_box:
        return
    
    box_data = fetch_box_data(selected_box)
    all_q_ids = [q_id for doc in box_data.values() for q_id in doc["QuestionIDs"]]
    questions = batch_get_questions(all_q_ids)
    
    if not box_data:
        st.error("Failed to load box data")
        return
    
    # Show_box interface
    st.header(f"📦 {selected_box}")
    
    # Statistics
    groups = {doc["WhichGroup"] for doc in box_data.values()}
    cols = st.columns(4)
    cols[0].metric("Documents", len(box_data))
    cols[1].metric("Questions", len(questions))
    cols[2].metric("Unique groups", len(groups))
    cols[3].metric("Last update", 
                  datetime.now().strftime("%d.%m.%Y %H:%M"))
    
    # Group filtering
    selected_group = st.sidebar.selectbox(
        "Filter by group", 
        ["All"] + sorted(groups))
    
    # Edit mode
    edit_mode = st.sidebar.checkbox("Edit mode")
    
    # Display documents with questions
    for doc_id, doc_data in box_data.items():
        if selected_group != "All" and doc_data["WhichGroup"] != selected_group:
            continue
            
        with st.expander(f"📄 Document: {doc_id} (Group: {doc_data['WhichGroup']})", True):
            # Group editing
            if edit_mode:
                if render_group_editor(doc_id, doc_data["WhichGroup"], doc_data["ref"]):
                    continue
            
            # Display questions
            for q_id in doc_data["QuestionIDs"]:
                if q_id not in questions:
                    continue
                    
                q_data = questions[q_id]
                with st.container(border=True):
                    cols = st.columns([4, 1])
                    cols[0].write(f"**{q_data.get('question', 'No text')}**")
                    cols[1].write(f"*Difficulty: {q_data.get('Question_Deficulity', '—')}*")
                    
                    st.write(f"**Answer:** {q_data.get('answer', 'No data')}")
                    
                    # Quick options preview
                    if any(key in q_data for key in ['A', 'B', 'C', 'D']):
                        st.write("**Options:**")
                        option_cols = st.columns(4)
                        for i, opt in enumerate(['A', 'B', 'C', 'D']):
                            if opt in q_data:
                                option_cols[i].write(f"{opt}) {q_data[opt]}")
                    
                    # Quick group edit button
                    if edit_mode:
                        with st.popover("✏️ Quick group edit"):
                            new_group = st.text_input(
                                "New group", 
                                value=doc_data["WhichGroup"],
                                key=f"quick_{doc_id}_{q_id}"
                            )
                            if st.button("Save", key=f"save_{doc_id}_{q_id}"):
                                update_group(doc_data["ref"], new_group)
                                st.rerun()
    
    # Analytics panel
    st.sidebar.divider()
    st.sidebar.header("📊 Analytics")
    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()
    
    # Data export
    if st.sidebar.button("📤 Export to CSV"):
        df = pd.DataFrame([
            {
                "ID": q_id,
                "Question": q_data.get("question", "")[:100],
                "Group": next(
                    (doc["WhichGroup"] for doc in box_data.values() 
                    if q_id in doc["QuestionIDs"]), "Unknown"),
                "Difficulty": q_data.get("Question_Deficulity", ""),
                "Topics": ", ".join(q_data.get("Topics", [])),
                "Usage count": q_data.get("usage_count", 0)
            } for q_id, q_data in questions.items()
        ])
        
        st.sidebar.download_button(
            label="Download CSV",
            data=df.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"questions_{selected_box}.csv",
            mime="text/csv"
        )


Show_box()