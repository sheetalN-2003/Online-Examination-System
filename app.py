import streamlit as st
import firebase_admin
from firebase_admin import auth, db, firestore
from firebase_config import db_firestore
import time
import datetime
from utils.auth import *
from utils.db_operations import *
from utils.exam_utils import *

# Page config
st.set_page_config(page_title="Online Exam System", layout="wide")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"

# Main App
def main():
    # Navigation
    if st.session_state.user is None:
        show_auth_pages()
    else:
        show_main_pages()

def show_auth_pages():
    """Show authentication pages (login, signup, forgot password)"""
    pages = {
        "Login": login_page,
        "Sign Up": signup_page,
        "Forgot Password": forgot_password_page
    }
    
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Display the selected page
    pages[selection]()

def show_main_pages():
    """Show main pages based on user role"""
    st.sidebar.title(f"Welcome, {st.session_state.user['email']}")
    
    if st.session_state.user_role == "admin":
        admin_pages = {
            "Dashboard": admin_dashboard,
            "Manage Users": manage_users,
            "Manage Exams": manage_exams,
            "Results": view_results
        }
        selection = st.sidebar.radio("Go to", list(admin_pages.keys()))
        admin_pages[selection]()
    else:
        student_pages = {
            "Dashboard": student_dashboard,
            "Take Exam": take_exam,
            "Results": view_student_results,
            "Leaderboard": view_leaderboard
        }
        selection = st.sidebar.radio("Go to", list(student_pages.keys()))
        student_pages[selection]()
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.user_role = None
        st.experimental_rerun()

# Run the app
if __name__ == "__main__":
    main()
