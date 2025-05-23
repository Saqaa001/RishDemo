import streamlit as st
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd
import requests
import plotly.express as px

# Constants
PASSWORD = "teacher123"
SUBJECTS = ["Math", "Science", "Physics", "Chemistry", "Biology"]
TEST_TYPES = ["All"]
DIFFICULTY_LEVELS = [str(i) for i in range(1, 11)]

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
def search_questions(search_query: str, subject_filter: str = None, difficulty_filter: str = None) -> bool:
    """Search for similar questions in the database with filters"""
    found = False
    
    with st.spinner("Searching database..."):
        subjects_to_search = [subject_filter] if subject_filter else SUBJECTS
        
        for science_type in subjects_to_search:
            questions_ref = db.collection("Questions").document(science_type).collection("All")
            query = questions_ref
            
            if search_query:
                query = query.where("question", ">=", search_query)\
                            .where("question", "<=", search_query + "\uf8ff")
            
            if difficulty_filter:
                query = query.where("Question_Deficulity", "==", difficulty_filter)
            
            questions = query.stream()
            
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
def get_questions_for_view(subject: str, test_type: str, search_query: str = "", 
                          difficulty_filter: str = None, topic_filter: List[str] = None) -> List[Dict]:
    """Get questions with optional search filtering"""
    questions_ref = db.collection("Questions").document(subject).collection(test_type)
    
    if search_query:
        questions_ref = questions_ref.where("question", ">=", search_query)\
                                    .where("question", "<=", search_query + "\uf8ff")
    
    if difficulty_filter:
        questions_ref = questions_ref.where("Question_Deficulity", "==", difficulty_filter)
    
    if topic_filter:
        questions_ref = questions_ref.where("Topics", "array_contains_any", topic_filter)
    
    questions = questions_ref.stream()
    
    return [{"id": q.id, **q.to_dict()} for q in questions]

def display_question_card(q: Dict) -> None:
    """Display question in an expandable card with enhanced formatting"""
    with st.expander(f"📝 Question ID: {q['id']}", expanded=False):
        # Main question
        st.markdown(f"**Question:** {q['question']}")
        
        # Answer options with color coding
        st.markdown("### Options:")
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"A: <span style='color:{'green' if q['answer']=='A' else 'black'}'>{q['A']}</span>", 
                       unsafe_allow_html=True)
            st.markdown(f"B: <span style='color:{'green' if q['answer']=='B' else 'black'}'>{q['B']}</span>", 
                       unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"C: <span style='color:{'green' if q['answer']=='C' else 'black'}'>{q['C']}</span>", 
                       unsafe_allow_html=True)
            st.markdown(f"D: <span style='color:{'green' if q['answer']=='D' else 'black'}'>{q['D']}</span>", 
                       unsafe_allow_html=True)
        
        # Metadata badges
        st.markdown("### Metadata:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Topics:** {', '.join(q.get('Topics', []))}")
        with col2:
            st.markdown(f"**Difficulty:** {q.get('Question_Deficulity', 'N/A')}")
        with col3:
            st.markdown(f"**Images:** {'🖼️' * len(q.get('Image', []))}")
        
        # Images display
        if q.get("Image"):
            st.markdown("### Attachments:")
            display_images(q["Image"], cols=4)

def add_topic_form() -> None:
    """Form to add new topics to ScienceTopics with document selection"""
    st.subheader("Add New Topic")
    existing_docs = get_existing_documents()
    topic_display = st.empty()

    with st.form("topic_form"):
        # Document selection or creation
        if existing_docs:
            document_name = st.selectbox(
                "Select Document",
                options=existing_docs,
                index=0,
                help="Select an existing document or type to search"
            )
        else:
            st.warning("No documents found in ScienceTopics collection")
            document_name = st.text_input("Create New Document Name", value="Math")

        # Fetch and display current topics
        if document_name:
            try:
                doc_ref = db.collection("ScienceTopics").document(document_name)
                current_topics = doc_ref.get().to_dict() or {}
                with topic_display.container():
                    if current_topics:
                        st.write("Current topics in this document:")
                       
                    else:
                        st.info("No topics found in this document")
            except Exception as e:
                topic_display.error(f"Failed to load document: {e}")

        # Topic fields
        col1, col2 = st.columns(2)
        with col1:
            topic_id = st.text_input(
                "Topic ID (must start with TID_)",
                value="TID_UX_GX_CX_T1",
                help="Format: TID_[category]_[subcategory]_[topicnum]"
            )
        with col2:
            topic_name = st.text_input("Topic Name", value="Topic 1")

        top_url = st.text_input("Topic URL (optional)", placeholder="https://example.com/topic")

        # Submit button
        if st.form_submit_button("Add Topic"):
            if not document_name:
                st.error("Please select or create a document")
                return
            if not topic_id.startswith("TID_") or not topic_name:
                st.error("Validation Error: Topic ID must start with 'TID_' and name must not be empty")
                return

            try:
                doc_ref = db.collection("ScienceTopics").document(document_name)
                current_data = doc_ref.get().to_dict() or {}

                topic_entry = {"name": topic_name}
                if top_url:
                    topic_entry["url"] = top_url

                if topic_id in current_data:
                    st.warning(f"Topic ID '{topic_id}' already exists in this document")
                    if not st.checkbox("Overwrite existing topic?"):
                        return

                doc_ref.set({topic_id: topic_entry}, merge=True)
                st.cache_data.clear()
                st.success(f"Topic '{topic_name}' ({topic_id}) added successfully!")

            except Exception as e:
                if "No document to update" in str(e):
                    try:
                        db.collection("ScienceTopics").document(document_name).set({
                            topic_id: topic_entry
                        })
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
        st.warning(f"🔍 Similar question found (ID: {question.id})")
        st.markdown(f"**Question:** {q_data.get('question')}")
        st.caption(f"Subject: {science_type} | Test: All")
        
        if q_data.get("Image"):
            display_images(q_data["Image"])

def display_images(image_urls: List[str], cols: int = 3) -> None:
    """Display images in responsive columns"""
    st.markdown("**Attached Images:**")
    columns = st.columns(min(cols, len(image_urls)))
    for idx, img in enumerate(image_urls[:cols*3]):  # Limit to 3 rows of images
        with columns[idx % cols]:
            try:
                st.image(img, width=150, caption=f"Image {idx+1}")
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
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("Search question database", key="question_search")
    with col2:
        subject_filter = st.selectbox("Filter by subject", [None] + SUBJECTS, format_func=lambda x: "All" if x is None else x)
    
    difficulty_filter = st.select_slider("Filter by difficulty", options=[None] + DIFFICULTY_LEVELS, 
                                       format_func=lambda x: "Any" if x is None else x)
    
    if st.button("Search") and (search_query or subject_filter or difficulty_filter):
        search_questions(search_query, subject_filter, difficulty_filter)
        st.session_state.search_performed = True

def Question_Def() -> str:
    """Get question difficulty"""
    return st.select_slider("Question Difficulty", options=DIFFICULTY_LEVELS, value="5")

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
    topic_names = {topic_id: topic["name"] for topic_id, topic in topics.items()}
    name_to_id = {v: k for k, v in topic_names.items()}
    
    selected_names = st.multiselect(
        "Related Topics (select multiple)",
        options=list(topic_names.values()),
        default=list(topic_names.values()) if topics else None
    )
    
    return [name_to_id[name] for name in selected_names]

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
    st.success(f"📁 {len(files)} file(s) selected")
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
    Question_Deficulity: str
) -> None:
    """Process and save the question data"""
    processed_urls = process_media_attachments(image_urls)
    question_data = create_question_data(
        science_type, test_type, topics, question_text,
        options, correct_answer, processed_urls, Question_Deficulity
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
    Question_Deficulity: str
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
        "Question_Deficulity": Question_Deficulity,
        "usage_count": 0,  # Track how often question is used
        "success_rate": 0.0  # Track student performance
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
    
    if st.button("➕ Add Another Question"):
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
    
    # Advanced filters
    with st.expander("🔍 Advanced Filters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            search_query = st.text_input("Search questions", key="view_search")
            topic_filter = st.multiselect("Filter by topic", options=list(get_topics().values()))
        with col2:
            difficulty_filter = st.select_slider("Filter by difficulty", 
                                              options=[None] + DIFFICULTY_LEVELS,
                                              format_func=lambda x: "Any" if x is None else x)
    
    questions = get_questions_for_view(
        selected_subject, 
        selected_test, 
        search_query,
        difficulty_filter,
        [k for k, v in get_topics().items() if v in topic_filter] if topic_filter else None
    )
    
    # Display question statistics
    if questions:
        display_question_statistics(questions)
    
    if not questions:
        st.info("No questions found for the selected criteria")
        return
    
    # Display the questions in cards or table view
    view_mode = st.radio("View Mode", ["Cards", "Table"], horizontal=True)
    
    if view_mode == "Cards":
        for q in questions:
            display_question_card(q)
    else:
        display_selectable_questions_table(questions, selected_subject, selected_test)

def display_question_statistics(questions: List[Dict]) -> None:
    """Display statistics and charts about the questions"""
    st.subheader("📊 Question Statistics")
    
    # Create DataFrame for analysis
    df = pd.DataFrame([
        {
            "Subject": q.get("science_type", "Unknown"),
            "Difficulty": int(q.get("Question_Deficulity", 0)),
            "Topics": len(q.get("Topics", [])),
            "Images": len(q.get("Image", [])),
            "Usage": q.get("usage_count", 0),
            "Success": q.get("success_rate", 0.0)
        } for q in questions
    ])
    
    if not df.empty:
        cols = st.columns(3)
        with cols[0]:
            st.metric("Total Questions", len(questions))
        with cols[1]:
            avg_diff = df["Difficulty"].mean()
            st.metric("Average Difficulty", f"{avg_diff:.1f}/10")
        with cols[2]:
            st.metric("Questions with Images", f"{len(df[df['Images'] > 0])} ({len(df[df['Images'] > 0])/len(df)*100:.0f}%)")
        
        # Visualizations
        tab1, tab2, tab3 = st.tabs(["Difficulty Distribution", "Subject Breakdown", "Topic Coverage"])
        
        with tab1:
            fig = px.histogram(df, x="Difficulty", nbins=10, 
                             title="Question Difficulty Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            subject_counts = df["Subject"].value_counts().reset_index()
            subject_counts.columns = ["Subject", "Count"]
            fig = px.pie(subject_counts, values="Count", names="Subject",
                        title="Questions by Subject")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            if "Topics" in df.columns:
                fig = px.box(df, y="Topics", title="Topics per Question")
                st.plotly_chart(fig, use_container_width=True)


def display_selectable_questions_table(questions: List[Dict], subject: str, test_type: str) -> None:
    """Display questions in a table with checkboxes for selection"""
    # Create DataFrame for display and convert numpy types to native Python types
    data = []
    for q in questions:
        data.append({
            "Select": False,
            "ID": str(q.get("id", "")),
            "Question": (str(q.get("question", "No question text"))[:100] + "..." 
                        if len(str(q.get("question", ""))) > 100 
                        else str(q.get("question", "No question text"))),
            "Correct Answer": str(q.get("answer", "")),
            "Topics": ", ".join(map(str, q.get("Topics", []))),
            "Images": int(len(q.get("Image", []))),
            "Difficulty": str(q.get("Question_Deficulity", "N/A")),
            "Created": str(q.get("created_at", ""))
        })
    
    df = pd.DataFrame(data)

    # Display editable table with checkboxes
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", help="Select questions", default=False),
            "Question": st.column_config.Column(width="large"),
            "ID": st.column_config.Column(width="small"),
            "Images": st.column_config.NumberColumn(
                "Images",
                help="Number of images attached",
                format="%d",
                min_value=0,
                max_value=5,
            ),
        },
        key="questions_table",
        disabled=["ID", "Question", "Correct Answer", "Topics", "Images", "Difficulty", "Created"]
    )

    # Filter selected rows
    selected_rows = edited_df[edited_df["Select"]]
    
    # Sidebar summary
    with st.sidebar:
        st.subheader("Selection Summary")
        st.metric("Selected Questions", len(selected_rows))
        if not selected_rows.empty:
            st.write("Preview of first selected:")
            st.write(selected_rows.iloc[0]["Question"][:100] + "...")

    # Batch actions section
    st.divider()
    st.subheader("Batch Actions")
    
    New_box = st.text_input("Create New Box For Students")
    WhichGroup = st.text_input("For Which Group")
    
    if st.button("💾 Add Selected Questions to Firestore"):
        if selected_rows.empty:
            st.warning("No questions selected.")
            return
        
        if not New_box:
            st.warning("Please enter a box name.")
            return
        
        question_ids = selected_rows["ID"].tolist()
        
        try:
            doc_ref = db.collection("Questions").document(subject).collection(New_box).document()
            doc_ref.set({
                "QuestionIDs": question_ids,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "WhichGroup": WhichGroup
            }, merge=True)

            st.success(f"✅ {len(question_ids)} question(s) added to {New_box}!")
            st.balloons()
        except Exception as e:
            st.error(f"Failed to save: {str(e)}")


def main() -> None:
    """Main application function"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .st-emotion-cache-1kyxreq {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .st-emotion-cache-1kyxreq img {
            border-radius: 8px;
            transition: transform 0.2s;
        }
        .st-emotion-cache-1kyxreq img:hover {
            transform: scale(1.05);
        }
        .stDataFrame {
            border-radius: 8px;
        }
        .stProgress > div > div > div {
            background-color: green;
        }
        [data-testid="stExpander"] {
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 1rem;
        }
        [data-testid="stExpander"]:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stMarkdown h3 {
            color: #2e86ab;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            border-radius: 4px 4px 0 0;
        }
        .stTabs [aria-selected="true"] {
            background-color: #f0f2f6;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🎓 Teacher Portal")
    
    if not authenticate():
        return
    
    render_sidebar()

def authenticate() -> bool:
    """Handle simple password authentication"""
    password = st.text_input("Enter Teacher Password", type="password", value="teacher123")
    if password != PASSWORD:
        st.warning("Please enter the correct password to access teacher features")
        return False
    return True

def View_Box_test():
    st.title("Math Questions Viewer")
    
    try:
        # Reference to the document containing QuestionIDs
        doc_ref = db.collection("Questions").document("Math")
        
        # Get the document with more detailed debugging
        st.write("Attempting to fetch document from: Questions/Math")
        doc = doc_ref.get()
        
        if not doc.exists:
            st.error("The specified Math document does not exist!")
            return
            
        data = doc.to_dict()
        st.write("Document data:", data)  # Debug output
        
        # Safely get values with defaults
        question_ids = data.get("QuestionIDs", [])
        which_group = data.get("WhichGroup", "Unknown Group")
        date = data.get("Date", "Unknown Date")
        
        st.subheader(f"Group: {which_group} - Date: {date}")
        st.write(f"Total Questions: {len(question_ids)}")
        
        if not question_ids:
            st.warning("No question IDs found in the document!")
            return
            
        # Get all questions from the "All" collection
        for i, qid in enumerate(question_ids, 1):
            try:
                st.write(f"\nFetching question {i}/{len(question_ids)}: {qid}")
                question_ref = db.collection("Questions").document("Math").collection("All").document(qid)
                question_doc = question_ref.get()
                
                if not question_doc.exists:
                    st.warning(f"Question with ID {qid} not found in 'All' collection!")
                    continue
                    
                question_data = question_doc.to_dict()
                st.write("Question data:", question_data)  # Debug output
                
                # Display each question in an expandable box
                with st.expander(f"Question {i}: {qid}"):
                    for key, value in question_data.items():
                        st.write(f"**{key}**: {value}")
                    st.write("---")
                    
            except Exception as e:
                st.error(f"Error processing question {qid}: {e}")
                continue
                
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error("Please check:")
        st.error("1. Firebase credentials are correct")
        st.error("2. Database structure matches expected format")
        st.error("3. Internet connection is active")


def render_sidebar() -> None:
    """Render sidebar navigation"""
    st.sidebar.title("📋 Teacher Menu")
    menu_option = st.sidebar.radio(
        "Options", 
        ["Add Topics", "Add Questions", "View Questions", "View Box test", "Student Analytics" ],
        key="teacher_menu"
    )
    
    if st.sidebar.button("🔄 Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
    
    if menu_option == "Add Topics":
        add_topic_form()

    elif menu_option == "Add Questions":
        add_question_form()

    elif menu_option == "View Questions":
        view_questions()
    
    # elif menu_option == "View Box test":
    #     View_Box_test()

    elif menu_option == "Student Analytics":
        st.info("Student analytics dashboard coming soon!")
        # Placeholder for future student analytics functionality
   
if __name__ == "__main__":
    db = get_db()
    main()