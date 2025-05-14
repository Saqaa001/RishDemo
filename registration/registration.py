import streamlit as st


st.subheader("Create New Account")

# Registration form
with st.form("registration_form"):
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    role = st.radio("Select your role:", ("Teacher", "Student", "Registration", "Admin"), horizontal=True)
    submitted = st.form_submit_button("Register")

# Handle form submission
if submitted:
    email = email.strip().lower()

    # Input validation
    if not all([email, username, password, confirm_password]):
        st.error("Please fill in all fields.")
    elif "@" not in email or "." not in email:
        st.error("Please enter a valid email address.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif len(password) < 6:
        st.error("Password must be at least 6 characters long.")
    else:
        with st.spinner("Registering user..."):
            success, message = firebase_auth.register_user(email, password, username, role)
            if success:
                st.success(message)
                st.session_state.show_login = True
                st.rerun()
            else:
                st.error(message)
