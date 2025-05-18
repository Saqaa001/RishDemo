import streamlit as st
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd
import requests

# Constants
PASSWORD = "teacher123"
SUBJECTS = ["Math", "Science", "Physics", "Chemistry", "Biology"]
TEST_TYPES = ["All"]

# Initialize Firestore connection with caching
@st.cache_resource
def get_db():
    """Cached Firestore connection"""
    return st.session_state.db

# Topic management with caching
@st.cache_data(ttl=3600)
def get_topics() -> Dict[str, str]:
    """Fetch available topics from ScienceTopics collection"""
    topics_ref = db.collection("ScienceTopics").document("Math")
    topics_doc = topics_ref.get()
    return {k: v for k, v in topics_doc.to_dict().items() 
            if k.startswith("TID") and v} if topics_doc.exists else {}

@st.cache_data(ttl=300)
def get_existing_documents():
    """Fetch and cache the list of existing documents in ScienceTopics collection"""
    try:
        return [doc.id for doc in db.collection("ScienceTopics").stream()]
    except Exception as e:
        st.error(f"Failed to fetch documents: {e}")
        return []

# Cached function for question search
@st.cache_data(ttl=300)
def search_questions(search_query: str) -> bool:
    """Search for similar questions in the database"""
    found = False
    
    with st.spinner("Searching database..."):
        for science_type in SUBJECTS:
            questions_ref = db.collection("Questions").document(science_type).collection("All")
            questions = questions_ref \
                .where(field_path="question", op_string=">=", value=search_query) \
                .where(field_path="question", op_string="<=", value=search_query + "\uf8ff") \
                .stream()
            
            for q in questions:
                display_question_result(q, science_type)
                found = True
    
    if not found:
        st.success("No similar questions found.")
    return found

# Cached function for image URL validation
@st.cache_data(ttl=600)
def validate_image_urls(urls: List[str]) -> List[str]:
    """Check if URLs are valid image links"""
    valid_urls = []
    with st.spinner("Validating URLs..."):
        for url in urls:
            try:
                response = requests.head(url, timeout=5)
                if 'image' in response.headers.get('content-type', ''):
                    valid_urls.append(url)
                    st.success(f"✅ Valid image: {url[:50]}...")
                else:
                    st.warning(f"⚠️ Not an image: {url[:50]}...")
            except:
                st.error(f"❌ Invalid URL: {url[:50]}...")
    return valid_urls

# Cached function for getting questions
@st.cache_data(ttl=60)
def get_questions(science_type: str, test_type: str) -> List[Dict]:
    """Get questions with caching"""
    questions_ref = db.collection("Questions").document(science_type).collection(test_type)
    return [doc.to_dict() for doc in questions_ref.stream()]

# Cached function for viewing questions
@st.cache_data(ttl=60)
def get_questions_for_view(subject: str, test_type: str, search_query: str = "") -> List[Dict]:
    """Get questions with optional search filtering"""
    questions_ref = db.collection("Questions").document(subject).collection(test_type)
    
    if search_query:
        questions = questions_ref \
            .where("question", ">=", search_query) \
            .where("question", "<=", search_query + "\uf8ff") \
            .stream()
    else:
        questions = questions_ref.stream()
    
    return [{"id": q.id, **q.to_dict()} for q in questions]

# Cached function for document creation check
@st.cache_data(ttl=300)
def check_document_exists(subject: str, box_name: str) -> bool:
    """Check if a document exists in Firestore"""
    doc_ref = db.collection("Questions").document(subject).collection(box_name).document()
    return doc_ref.get().exists

def add_topic_form() -> None:
    """Form to add new topics to ScienceTopics with document selection"""
    st.subheader("Add New Topic")
    existing_docs = get_existing_documents()
    topic_display = st.empty()
    
    with st.form("topic_form"):
        if existing_docs:
            document_name = st.selectbox(
                "Select Document",
                options=existing_docs,
                index=0,
                help="Select an existing document or type to search"
            )
            
            try:
                doc_ref = db.collection("ScienceTopics").document(document_name)
                current_topics = doc_ref.get().to_dict() or {}
                if current_topics:
                    with topic_display.container():
                        st.write("Current topics in this document:")
                        st.json(current_topics)
                else:
                    topic_display.info("No topics found in this document")
            except Exception as e:
                topic_display.error(f"Failed to load document: {e}")
        else:
            st.warning("No documents found in ScienceTopics collection")
            document_name = st.text_input("Create New Document Name", value="Math")
        
        col1, col2 = st.columns(2)
        with col1:
            topic_id = st.text_input(
                "Topic ID (must start with TID_)", 
                value="TID_UX_GX_CX_T1",
                help="Format: TID_[category]_[subcategory]_[topicnum]"
            )
        with col2:
            topic_name = st.text_input("Topic Name", value="Topic 1")
        
        if st.form_submit_button("Add Topic"):
            if not document_name:
                st.error("Please select or create a document")
                return
            if not (topic_id.startswith("TID_") and topic_name):
                st.error("Validation Error: Topic ID must start with TID_ and Name cannot be empty")
                return
            
            try:
                doc_ref = db.collection("ScienceTopics").document(document_name)
                current_data = doc_ref.get().to_dict() or {}
                if topic_id in current_data:
                    st.warning(f"Topic ID '{topic_id}' already exists in this document")
                    if not st.checkbox("Overwrite existing topic?"):
                        return
                
                doc_ref.update({topic_id: topic_name})
                topic_display.empty()
                with topic_display.container():
                    updated_topics = doc_ref.get().to_dict() or {}
                    if updated_topics:
                        st.write("Updated topics in this document:")
                        st.json(updated_topics)
                    else:
                        st.info("No topics found in this document")
                
                st.cache_data.clear()
                st.success(f"Topic '{topic_name}' ({topic_id}) added successfully!")
                
            except Exception as e:
                if "No document to update" in str(e):
                    try:
                        db.collection("ScienceTopics").document(document_name).set({topic_id: topic_name})
                        topic_display.empty()
                        st.cache_data.clear()
                        st.success(f"Created new document '{document_name}' with first topic!")
                    except Exception as create_error:
                        st.error(f"Failed to create document: {create_error}")
                else:
                    st.error(f"Database Error: {e}")

def display_question_result(question, science_type: str) -> None:
    """Display question search result"""
    q_data = question.to_dict()
    with st.container(border=True):
        st.warning(f"Similar question found (ID: {question.id})")
        st.markdown(f"**Question:** {q_data.get('question')}")
        st.caption(f"Subject: {science_type} | Test: All")
        
        if q_data.get("Image"):
            display_images(q_data["Image"])

def display_images(image_urls: List[str], cols: int = 3) -> None:
    """Display images in columns"""
    st.markdown("**Attached Images:**")
    columns = st.columns(min(cols, len(image_urls)))
    for idx, img in enumerate(image_urls[:cols]):
        with columns[idx % cols]:
            try:
                st.image(img, width=150)
            except:
                st.markdown(f"📎 [Image Link]({img})")

def add_question_form() -> None:
    """Form to add new questions with search and media handling"""
    st.title("📝 Add New Question")
    initialize_session_state()
    
    with st.expander("🔍 Check for existing questions (optional)", expanded=False):
        handle_question_search()
    
    with st.form("question_form", clear_on_submit=True):
        if render_question_form():
            st.form_submit_button("💾 Save Question")

def initialize_session_state() -> None:
    """Initialize session state variables"""
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False

def handle_question_search() -> None:
    """Handle question search functionality"""
    search_query = st.text_input("Search question database", key="question_search")
    if st.button("Search") and search_query:
        search_questions(search_query)
        st.session_state.search_performed = True

def Question_Def()-> None:
    select_Q_D = st.text_input("Question_Deficulity")
    return select_Q_D


def render_question_form() -> bool:
    """Render the question form and return True if valid"""
    st.markdown("### Question Details")
    science_type, test_type = render_subject_selection()
    topic_ids = render_topic_selection()
    Question_Deficulity = Question_Def()
    question_text = render_question_text()
    options, correct_answer = render_answer_options()
    image_urls = handle_media_upload()
    
    if st.form_submit_button():
        return validate_and_submit(
            science_type, test_type, topic_ids, question_text, 
            options, correct_answer, image_urls, Question_Deficulity
        )
    return False

def render_subject_selection() -> Tuple[str, str]:
    """Render subject and test type selection"""
    col1, col2 = st.columns(2)
    with col1:
        science_type = st.selectbox("Subject", SUBJECTS, index=0)
    with col2:
        test_type = st.selectbox("Test Type", TEST_TYPES, index=0)
    return science_type, test_type

def render_topic_selection() -> List[str]:
    """Render topic multi-select and return selected topic IDs"""
    topics = get_topics()
    selected_topics = st.multiselect(
        "Related Topics (select multiple)",
        options=list(topics.values()),
        default=list(topics.values())[:1] if topics else None
    )
    return [k for k, v in topics.items() if v in selected_topics]

def render_question_text() -> str:
    """Render question text area with search auto-fill"""
    return st.text_area(
        "Question Text *", 
        value=st.session_state.get("question_search", ""),
        height=100,
        placeholder="Enter your question here..."
    )

def render_answer_options() -> Tuple[List[str], str]:
    """Render answer options and correct answer selection"""
    st.markdown("### Answer Options")
    ans_col1, ans_col2 = st.columns(2)
    with ans_col1:
        option_a = st.text_input("Option A *", placeholder="First answer choice")
        option_b = st.text_input("Option B *", placeholder="Second answer choice")
    with ans_col2:
        option_c = st.text_input("Option C *", placeholder="Third answer choice")
        option_d = st.text_input("Option D *", placeholder="Fourth answer choice")
    
    correct_answer = st.radio(
        "Correct Answer *",
        ["A", "B", "C", "D"],
        horizontal=True,
        index=0
    )
    return [option_a, option_b, option_c, option_d], correct_answer

def validate_and_submit(*args) -> bool:
    """Validate form and submit if valid"""
    if not all(args[3]) or not all(args[4]):
        st.error("Please fill all required fields (marked with *)")
        return False
    handle_form_submission(*args)
    return True

def handle_media_upload() -> List[Tuple[str, any]]:
    """Handle image uploads and URL inputs"""
    image_urls = []
    tab_upload, tab_url = st.tabs(["📤 Upload Images", "🔗 Paste URLs"])
    
    with tab_upload:
        uploaded_files = st.file_uploader(
            "Choose image files (max 5 MB each)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True
        )
        if uploaded_files:
            image_urls.extend(("upload", file) for file in uploaded_files[:5])
            display_uploaded_images(uploaded_files)
    
    with tab_url:
        url_input = st.text_area(
            "Enter image URLs (one per line)",
            height=100,
            placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.png"
        )
        if url_input.strip():
            urls = [url.strip() for url in url_input.split('\n') if url.strip()]
            image_urls.extend(("url", url) for url in urls)
            if st.button("Validate URLs"):
                validate_image_urls(urls)
    
    return image_urls

def display_uploaded_images(files: List) -> None:
    """Display uploaded images in columns"""
    st.success(f"{len(files)} file(s) selected")
    cols = st.columns(min(4, len(files)))
    for idx, file in enumerate(files[:5]):
        with cols[idx % 4]:
            st.image(file, caption=f"Image {idx+1}", width=120)

def handle_form_submission(
    science_type: str,
    test_type: str,
    topics: List[str],
    question_text: str,
    options: List[str],
    correct_answer: str,
    image_urls: List[Tuple[str, any]],
    Question_Deficulity: str  # Add this parameter
) -> None:
    """Process and save the question data"""
    processed_urls = process_media_attachments(image_urls)
    question_data = create_question_data(
        science_type, test_type, topics, question_text,
        options, correct_answer, processed_urls, Question_Deficulity  # Add the parameter here
    )
    
    try:
        save_question_to_firestore(science_type, test_type, question_data)
        show_success_message(question_text, correct_answer, processed_urls)
    except Exception as e:
        st.error(f"Error saving question: {str(e)}")





def process_media_attachments(image_urls: List[Tuple[str, any]]) -> List[str]:
    """Process uploaded files and URLs into public URLs"""
    processed_urls = []
    for media_type, content in image_urls:
        if media_type == "upload":
            processed_urls.append(upload_to_storage(content))
        else:
            processed_urls.append(content)
    return processed_urls

def upload_to_storage(file) -> str:
    """Upload file to Firebase Storage and return public URL"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"questions/{timestamp}_{file.name}"
        blob = storage.bucket().blob(filename)
        blob.upload_from_string(file.getvalue(), content_type=file.type)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        st.error(f"Failed to upload {file.name}: {str(e)}")
        return ""

def create_question_data(
    science_type: str,
    test_type: str,
    topics: List[str],
    question_text: str,
    options: List[str],
    correct_answer: str,
    image_urls: List[str],
    Question_Deficulity: str  # Add this parameter
) -> Dict:
    """Create question data dictionary"""
    return {
        "question": question_text,
        "A": options[0],
        "B": options[1],
        "C": options[2],
        "D": options[3],
        "answer": correct_answer,
        "Image": image_urls,
        "Topics": topics,
        "science_type": science_type,
        "test_type": test_type,
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "Question_Deficulity": Question_Deficulity  # Add this field
    }


def save_question_to_firestore(science_type: str, test_type: str, data: Dict) -> None:
    """Save question to Firestore"""
    with st.spinner("Saving question..."):
        questions_ref = db.collection("Questions").document(science_type).collection(test_type)
        new_question_ref = questions_ref.add(data)
        questions_ref.document(new_question_ref[1].id).update({"QID": new_question_ref[1].id})
    st.cache_data.clear()

def show_success_message(question: str, answer: str, images: List[str]) -> None:
    """Display success message and question preview"""
    st.toast("Question saved successfully!", icon="✅")
    st.success("### Question saved successfully!")
    
    with st.expander("View Saved Question", expanded=True):
        st.markdown(f"**Question:** {question}")
        st.markdown(f"**Correct Answer:** {answer}")
        if images:
            display_images(images, cols=4)
    
    if st.button("Add Another Question"):
        st.session_state.search_performed = False
        st.rerun()

def view_questions():
    """View and manage existing questions with selection capabilities"""
    st.title("📚 View Questions")
    
    # Initialize session state for selected questions
    if 'selected_questions' not in st.session_state:
        st.session_state.selected_questions = set()
    
    col1, col2 = st.columns(2)
    with col1:
        selected_subject = st.selectbox("Select Subject", SUBJECTS, key="view_subject")
    with col2:
        selected_test = st.selectbox("Select Test Type", TEST_TYPES, key="view_test")
    
    search_query = st.text_input("Search questions", key="view_search")
    questions = get_questions_for_view(selected_subject, selected_test, search_query)
    
    if not questions:
        st.info("No questions found for the selected criteria")
        return
    
    # Display the questions table with checkboxes
    display_selectable_questions_table(questions, selected_subject, selected_test)

def display_selectable_questions_table(questions: List[Dict], subject: str, test_type: str) -> None:
    """Display questions in a table with checkboxes for selection, and add selected ones to Firestore"""
    # Create DataFrame for display with safe access to dictionary keys
    df = pd.DataFrame([
        {
            "Select": False,
            "ID": q.get("id", ""),
            "Question": (q.get("question", "No question text")[:100] + "..." 
                        if len(q.get("question", "")) > 100 
                        else q.get("question", "No question text")),
            "Correct Answer": q.get("answer", ""),
            "Topics": ", ".join(q.get("Topics", [])),
            "Images": len(q.get("Image", [])),
            "Created": q.get("created_at", ""),
        } for q in questions
    ])

    # Display editable table with checkboxes
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", help="Select questions", default=False),
            "Question": st.column_config.Column(width="large"),
            "ID": st.column_config.Column(width="small"),
        },
        key="questions_table",
        disabled=["ID", "Question", "Correct Answer", "Topics", "Images", "Created"]
    )

    # Filter selected rows
    selected_rows = edited_df[edited_df["Select"]]

    st.write("Selected Questions")
    st.dataframe(selected_rows)
    
    New_box = st.text_input("Create New Box For Students")
    WhichGroup = st.text_input("For Which Group")
    
    # Add button to upload selected questions to Firestore
    if st.button("Add Selected Questions to Firestore"):
        if selected_rows.empty:
            st.warning("No questions selected.")
            return
        
        if not New_box:
            st.warning("Please enter a box name.")
            return
        
        # Get all selected question IDs
        question_ids = selected_rows["ID"].tolist()
        
        # Create or update the document with an array of question IDs
        doc_ref = db.collection("Questions").document(subject).collection(New_box).document()
        doc_ref.set({
            "QuestionIDs": question_ids,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "WhichGroup": WhichGroup
        }, merge=True)

        st.success(f"{len(question_ids)} question(s) added to {New_box} in Firestore.")

def delete_selected_questions(subject: str, test_type: str) -> None:
    """Delete all selected questions"""
    if not st.session_state.selected_questions:
        st.warning("No questions selected")
        return
    
    if st.checkbox("⚠️ Confirm permanent deletion of selected questions"):
        progress_bar = st.progress(0)
        total = len(st.session_state.selected_questions)
        
        for i, qid in enumerate(st.session_state.selected_questions):
            try:
                db.collection("Questions").document(subject).collection(test_type).document(qid).delete()
                progress_bar.progress((i + 1) / total)
            except Exception as e:
                st.error(f"Failed to delete question {qid}: {str(e)}")
        
        st.success(f"Deleted {len(st.session_state.selected_questions)} questions successfully!")
        st.session_state.selected_questions = set()
        st.cache_data.clear()
        st.rerun()

def display_questions_table(questions: List[Dict], subject: str, test_type: str) -> None:
    """Display questions in an interactive table with management options"""
    display_data = []
    for q in questions:
        display_data.append({
            "ID": q["id"],
            "Question": q["question"][:100] + "..." if len(q["question"]) > 100 else q["question"],
            "Correct Answer": q["answer"],
            "Topics": ", ".join(q.get("Topics", [])),
            "A": q["D"],
            "B": q["B"],
            "C": q["C"],
            "D": q["D"],
            "Images": len(q.get("Image", [])),
            "Created": q.get("created_at", ""),
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Actions": st.column_config.Column(
                "Actions",
                help="Manage question",
                width="small"
            ),
            "Question": st.column_config.Column(
                width="large"
            )
        }
    )
    
def delete_question(subject: str, test_type: str, question_id: str) -> None:
    """Delete a question from Firestore"""
    try:
        db.collection("Questions").document(subject).collection(test_type).document(question_id).delete()
        st.success(f"Question {question_id} deleted successfully!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error deleting question: {str(e)}")

def main() -> None:
    """Main application function"""
    st.title("Teacher Portal")
    
    if not authenticate():
        return
    
    render_sidebar()

def authenticate() -> bool:
    """Handle simple password authentication"""
    password = st.text_input("Enter Teacher Password", type="password")
    if password != PASSWORD:
        st.warning("Please enter the correct password to access teacher features")
        return False
    return True

def render_sidebar() -> None:
    """Render sidebar navigation"""
    st.sidebar.title("Teacher Menu")
    menu_option = st.sidebar.radio(
        "Options", 
        ["Add Topics", "Add Questions", "View Questions"],
        key="teacher_menu"
    )
    
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
    
    if menu_option == "Add Topics":
        add_topic_form()
    elif menu_option == "Add Questions":
        add_question_form()
    elif menu_option == "View Questions":
        view_questions()

if __name__ == "__main__":
    db = get_db()
    main()