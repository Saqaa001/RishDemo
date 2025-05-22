import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin import exceptions as firebase_exceptions

def initialize_firebase():
    """Initialize Firebase app if not already initialized."""
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate('.streamlit/firebase.json')
            firebase_admin.initialize_app(cred)
        except (ValueError, FileNotFoundError) as e:
            st.error(f"Failed to initialize Firebase: {str(e)}")
            st.stop()

def validate_input(email: str, username: str, password: str, confirm_password: str) -> tuple:
    """Validate user registration input."""
    if not all([email, username, password, confirm_password]):
        return False, "Please fill in all fields."
    if "@" not in email or "." not in email:
        return False, "Please enter a valid email address."
    if password != confirm_password:
        return False, "Passwords do not match."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, "Validation successful"

def register_user(email: str, password: str, username: str, role: str) -> tuple:
    """Register a new user with Firebase Authentication and Firestore."""
    try:
        # Create Firebase auth user
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Store additional user data in Firestore
        db = firestore.client()
        user_ref = db.collection('Student').document(user.uid)
        user_ref.set({
            'username': username,
            'email': email,
            'role': role,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        return True, "Registration successful!"
    
    except auth.EmailAlreadyExistsError:
        return False, "Email already exists."
    except auth.UidAlreadyExistsError:
        return False, "User ID already exists."
    except firebase_exceptions.FirebaseError as e:
        return False, f"Firebase error: {str(e)}"
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"

# Initialize Firebase
initialize_firebase()

# Registration UI
def show_registration_form():
    """Display the user registration form."""
    st.subheader("Create New Account")
    
    with st.form("registration_form"):
        email = st.text_input("Email").strip().lower()
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.radio(
            "Select your role:",
            ("Teacher", "Student", "Registration", "Admin"),
            horizontal=True
        )
        submitted = st.form_submit_button("Register")

        if submitted:
            is_valid, validation_msg = validate_input(email, username, password, confirm_password)
            
            if not is_valid:
                st.error(validation_msg)
            else:
                with st.spinner("Registering user..."):
                    success, message = register_user(email, password, username, role)
                    
                    if success:
                        st.success(message)
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error(message)

# Main execution
if __name__ == "__main__":
    show_registration_form()