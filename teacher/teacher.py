import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
from typing import List, Dict, Tuple, Optional

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


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_existing_documents():
    """Fetch and cache the list of existing documents in ScienceTopics collection"""
    try:
        return [doc.id for doc in db.collection("ScienceTopics").stream()]
    except Exception as e:
        st.error(f"Failed to fetch documents: {e}")
        return []

@st.cache_data(ttl=300)
def get_existing_documents():
    """Fetch and cache the list of existing document names"""
    try:
        docs = db.collection("ScienceTopics").stream()
        return [doc.id for doc in docs]
    except Exception as e:
        st.error(f"Failed to fetch documents: {e}")
        return []

def add_topic_form() -> None:
    """Form to add new topics to ScienceTopics with document selection"""
    st.subheader("Add New Topic")
    
    existing_docs = get_existing_documents()
    topic_display = st.empty()  # Placeholder for topics display
    
    with st.form("topic_form"):
        # Document selection with search capability
        if existing_docs:
            document_name = st.selectbox(
                "Select Document",
                options=existing_docs,
                index=0,
                help="Select an existing document or type to search"
            )
            
            # Show topics in selected document
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
        
        # Topic input fields
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
            # Validation
            if not document_name:
                st.error("Please select or create a document")
                return
            if not (topic_id.startswith("TID_") and topic_name):
                st.error("Validation Error: Topic ID must start with TID_ and Name cannot be empty")
                return
            
            try:
                doc_ref = db.collection("ScienceTopics").document(document_name)
                
                # Check if topic ID already exists
                current_data = doc_ref.get().to_dict() or {}
                if topic_id in current_data:
                    st.warning(f"Topic ID '{topic_id}' already exists in this document")
                    if not st.checkbox("Overwrite existing topic?"):
                        return
                
                # Update document
                doc_ref.update({topic_id: topic_name})
                
                # Clear and refresh display
                topic_display.empty()
                with topic_display.container():
                    updated_topics = doc_ref.get().to_dict() or {}
                    if updated_topics:
                        st.write("Updated topics in this document:")
                        st.json(updated_topics)
                    else:
                        st.info("No topics found in this document")
                
                # Clear caches
                st.cache_data.clear()
                st.success(f"Topic '{topic_name}' ({topic_id}) added successfully!")
                
            except Exception as e:
                if "No document to update" in str(e):
                    # Document doesn't exist, create it first
                    try:
                        db.collection("ScienceTopics").document(document_name).set({topic_id: topic_name})
                        topic_display.empty()
                        st.cache_data.clear()
                        st.success(f"Created new document '{document_name}' with first topic!")
                    except Exception as create_error:
                        st.error(f"Failed to create document: {create_error}")
                else:
                    st.error(f"Database Error: {e}")


@st.cache_data(ttl=300)
def search_questions(search_query: str) -> bool:
    """Search for similar questions in the database"""
    found = False
    
    with st.spinner("Searching database..."):
        for science_type in SUBJECTS:
            questions_ref = db.collection("Questions").document(science_type).collection("All")
            questions = questions_ref.where(field_path="question", op_string=">=", value=search_query) \
                                     .where(field_path="question", op_string="<=", value=search_query + "\uf8ff") \
                                     .stream()
            
            for q in questions:
                display_question_result(q, science_type)
                found = True
    
    if not found:
        st.success("No similar questions found.")
    return found


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

@st.cache_data(ttl=60)
def get_questions(science_type: str, test_type: str) -> List[Dict]:
    """Get questions with caching"""
    questions_ref = db.collection("Questions").document(science_type).collection(test_type)
    return [doc.to_dict() for doc in questions_ref.stream()]

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

def render_question_form() -> bool:
    """Render the question form and return True if valid"""
    st.markdown("### Question Details")
    science_type, test_type = render_subject_selection()
    topic_ids = render_topic_selection()
    question_text = render_question_text()
    options, correct_answer = render_answer_options()
    image_urls = handle_media_upload()
    
    if st.form_submit_button():
        return validate_and_submit(
            science_type, test_type, topic_ids, question_text, 
            options, correct_answer, image_urls
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
    if not all(args[3]) or not all(args[4]):  # Check question text and options
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
    image_urls: List[Tuple[str, any]]
) -> None:
    """Process and save the question data"""
    processed_urls = process_media_attachments(image_urls)
    question_data = create_question_data(
        science_type, test_type, topics, question_text,
        options, correct_answer, processed_urls
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

def create_question_data(*args) -> Dict:
    """Create question data dictionary"""
    return {
        "question": args[3],
        "A": args[4][0],
        "B": args[4][1],
        "C": args[4][2],
        "D": args[4][3],
        "answer": args[5],
        "Image": args[6],
        "Topics": args[2],
        "science_type": args[0],
        "test_type": args[1],
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat()
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

def view_questions() -> None:
    """Display existing questions from the database"""
    st.subheader("View Questions")
    science_type, test_type = render_question_filters()
    questions = get_questions(science_type, test_type)
    
    if not questions:
        st.warning("No questions found for this selection.")
        return
    
    df = create_questions_dataframe(questions)
    display_questions_table(df)
    display_question_details(df)
    add_download_button(df, science_type, test_type)

def render_question_filters() -> Tuple[str, str]:
    """Render filters for question viewing"""
    col1, col2 = st.columns(2)
    with col1:
        science_type = st.selectbox("Select Science Type", SUBJECTS, index=1)
    with col2:
        test_type = st.selectbox("Select Test Type", TEST_TYPES, index=0)
    return science_type, test_type

def create_questions_dataframe(questions: List[Dict]) -> pd.DataFrame:
    """Create DataFrame from questions data"""
    topics = get_topics()
    df_data = []
    
    for question in questions:
        images = question.get("Image", [])
        df_data.append({
            "QID": question.get("QID", "N/A"),
            "Question": question.get("question", "N/A"),
            "Subject": question.get("science_type", "N/A"),
            "Test Type": question.get("test_type", "N/A"),
            "Topics": ", ".join(topics.get(tid, tid) for tid in question.get("Topics", [])),
            "Option A": question.get("A", ""),
            "Option B": question.get("B", ""),
            "Option C": question.get("C", ""),
            "Option D": question.get("D", ""),
            "Correct Answer": question.get("answer", "N/A"),
            "Created At": question.get("created_at", "N/A"),
            "Image Count": int(len(images)) if isinstance(images, (list, tuple)) else 0,
            "Images": images if isinstance(images, (list, tuple)) else []
        })
    
    return pd.DataFrame(df_data)

def display_questions_table(df: pd.DataFrame) -> None:
    """Display questions in an interactive table"""
    st.dataframe(
        df.drop(columns=["Images"]),
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "Image Count": st.column_config.NumberColumn(
                "Images",
                help="Number of attached images",
                format="%d 📷"
            ),
            "Created At": st.column_config.DatetimeColumn(
                "Created",
                format="YYYY-MM-DD HH:mm"
            )
        }
    )

def display_question_details(df: pd.DataFrame) -> None:
    """Display detailed view of selected question"""
    st.subheader("Question Details")
    selected_qid = st.selectbox(
        "Select Question to View Details",
        options=df["QID"],
        index=0,
        format_func=lambda x: f"QID: {x}"
    )
    
    selected_question = df[df["QID"] == selected_qid].iloc[0]
    
    with st.expander("View Full Question", expanded=True):
        render_question_detail_view(selected_question)

def render_question_detail_view(question: pd.Series) -> None:
    """Render detailed view of a single question"""
    st.markdown(f"**Question:** {question['Question']}")
    st.markdown(f"**Subject:** {question['Subject']}")
    st.markdown(f"**Test Type:** {question['Test Type']}")
    st.markdown(f"**Topics:** {question['Topics']}")
    
    st.markdown("**Options:**")
    for option in ['A', 'B', 'C', 'D']:
        st.markdown(f"- {option}) {question[f'Option {option}']}")
    
    st.markdown(f"**Correct Answer:** {question['Correct Answer']}")
    
    if question["Image Count"] > 0:
        display_images(question["Images"])

def add_download_button(df: pd.DataFrame, science_type: str, test_type: str) -> None:
    """Add CSV download button for questions"""
    csv = df.drop(columns=["Images"]).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Questions as CSV",
        data=csv,
        file_name=f"questions_{science_type}_{test_type}.csv",
        mime="text/csv"
    )

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