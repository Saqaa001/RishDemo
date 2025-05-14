import streamlit as st

st.header("Settings")


role = st.session_state.role
if role == "Student":
    st.write(f"You are {role}")
    st.write("4444444")
if role == "Teacher":
    st.write(f"You are {role}")
    st.write("333333333")
if role == "Admin":
    st.write(f"You are {role}")
    st.write("22222222")
if role == "Registration":
    st.write(f"You are {role}")
    st.write("111111111")