import streamlit as st
import requests
from streamlit_cookies_manager import EncryptedCookieManager
from uuid import uuid4
import firebase_admin
from firebase_admin import credentials, firestore, auth

# === Configuration ===
SERVICE_ACCOUNT_FILE = ".streamlit/firebase.json"
FIREBASE_WEB_API_KEY = "AIzaSyCj0UPv444P-C6ggFZ8Q_NXvSSBraHeDG4"
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"



ROLES = ["Registration", "Student", "Teacher", "Admin", None]

# === Cached Firebase Setup ===
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()
if db not in st.session_state:
    st.session_state['db'] = db


# === Firebase Auth ===
@st.cache_data(show_spinner=True)
def verify_user(email: str, password: str, user_type: str):
    try:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(FIREBASE_AUTH_URL, json=payload)
        data = response.json()

        if response.status_code == 200:
            user_id = data.get("localId")
            if user_id:
                doc = db.collection(user_type).document(user_id).get()
                if doc.exists:
                    return True, "Authentication successful", doc.to_dict()
                return False, "User data not found", None
            return False, "User ID not found", None
        return False, data.get("error", {}).get("message", "Authentication failed"), None

    except Exception as e:
        return False, f"Authentication failed: {str(e)}", None


def register_user(email, password, username, role):
    try:
        user = auth.create_user(email=email, password=password, uid=str(uuid4()))
        user_data = {
            'username': username,
            'role': role,
            'email': email,
            'uid': user.uid
        }
        db.collection('users').document(user.uid).set(user_data)
        return True, "Registration successful"
    except auth.EmailAlreadyExistsError:
        return False, "Email already exists"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"


# === Cookie Handling ===
cookies = EncryptedCookieManager(
    prefix="my_app/",
    password="8929239608489292396084"  # Use env variable in production
)

if not cookies.ready():
    st.stop()

# Initialize session state from cookies
for key in ["role", "user_id", "email"]:
    if key not in st.session_state:
        st.session_state[key] = cookies.get(key)

# === UI Pages ===
def login():
    st.header("Log in")

    email = st.text_input("Email", value="sshax1015@gmail.com")
    password = st.text_input("Password", type="password", value="123456789")
    role = st.selectbox("Choose your role", [r for r in ROLES if r])

    if st.button("Log in"):
        with st.spinner("Authenticating..."):
            success, message, user_data = verify_user(email, password, role)

            if success:
                for key in ["role", "user_id"]:
                    val = user_data.get(key)
                    if val:
                        st.session_state[key] = val
                        cookies[key] = str(val)

                st.session_state["email"] = email
                cookies["email"] = str(email)
                cookies.save()

                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(f"Login failed: {message}")


def logout():
    for key in ["role", "user_id", "email"]:
        st.session_state[key] = None
        cookies[key] = ""
    cookies.save()
    st.success("Logged out successfully!")
    st.cache_data.clear()
    st.rerun()


# === Page Routing ===
def get_pages():
    from streamlit import Page
    return {
        "Student": [
            Page("student/student.py", title="Student", icon="🎓", default=st.session_state.role == "Student")
        ],
        "Teacher": [
            Page("teacher/teacher.py", title="Teacher", icon="👩‍🏫", default=st.session_state.role == "Teacher")
        ],
        "Admin": [
            Page("admin/admin.py", title="Admin", icon="👨‍💼", default=st.session_state.role == "Admin")
        ],
        "Registration": [
            Page("registration/registration.py", title="Registration", icon="📝", default=st.session_state.role == "Registration")
        ],
        "Account": [
            Page("settings.py", title="Settings", icon="⚙️"),
            Page(logout, title="Log out", icon="🚪"),
        ]
    }


def main():
    from streamlit import navigation, Page

    if not st.session_state.role:
        navigation([Page(login, title="Login")]).run()
        return

    pages = get_pages()
    available_pages = {
        section: items for section, items in pages.items()
        if section == st.session_state.role or section == "Account"
    }

    if available_pages:
        navigation(available_pages).run()
    else:
        st.error("No pages available for your role.")
        if st.button("Logout"):
            logout()


if __name__ == "__main__":
    main()
