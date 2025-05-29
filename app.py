import streamlit as st
from utils.auth import login_page, signup_page, forgot_password_page, logout
from utils.exam_utils import (
    admin_dashboard, 
    manage_users, 
    manage_exams, 
    view_results,  
    student_dashboard, 
    take_exam, 
    view_student_results, 
    view_leaderboard
)
)
from firebase_config import is_firebase_initialized
import time

# App configuration
st.set_page_config(
    page_title="Online Exam System",
    page_icon="📝",
    layout="wide"
)

def main():
    # Check Firebase initialization
    if not is_firebase_initialized():
        st.error("Firebase initialization failed. Please check your configuration.")
        return

    # Session state initialization
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # Navigation
    if 'user' in st.session_state:
        # User is logged in - show appropriate dashboard
        if st.session_state.user['role'] == 'admin':
            show_admin_interface()
        else:
            show_student_interface()
    else:
        # User is not logged in - show auth pages
        show_auth_pages()

def show_auth_pages():
    """Show authentication pages based on current page state"""
    # Sidebar for auth navigation
    st.sidebar.title("Online Exam System")
    
    # Page selection
    if st.session_state.page == "login":
        login_page()
        if st.sidebar.button("Don't have an account? Sign up"):
            st.session_state.page = "signup"
            st.experimental_rerun()
        if st.sidebar.button("Forgot password?"):
            st.session_state.page = "forgot_password"
            st.experimental_rerun()
            
    elif st.session_state.page == "signup":
        signup_page()
        if st.sidebar.button("Already have an account? Login"):
            st.session_state.page = "login"
            st.experimental_rerun()
            
    elif st.session_state.page == "forgot_password":
        forgot_password_page()
        if st.sidebar.button("Back to login"):
            st.session_state.page = "login"
            st.experimental_rerun()

def show_admin_interface():
    """Show admin dashboard and navigation"""
    st.sidebar.title(f"Welcome, {st.session_state.user['display_name']}")
    st.sidebar.subheader("Admin Dashboard")
    
    # Admin navigation
    menu_options = {
        "Dashboard": admin_dashboard,
        "User Management": manage_users,
        "Exam Management": manage_exams,
        "View Results": view_results
    }
    
    choice = st.sidebar.radio("Menu", list(menu_options.keys()))
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
    
    # Display selected page
    menu_options[choice]()

def show_student_interface():
    """Show student dashboard and navigation"""
    st.sidebar.title(f"Welcome, {st.session_state.user['display_name']}")
    st.sidebar.subheader("Student Dashboard")
    
    # Student navigation
    menu_options = {
        "Dashboard": student_dashboard,
        "Take Exam": take_exam,
        "My Results": view_student_results,
        "Leaderboard": view_leaderboard
    }
    
    # Special case for take exam page
    if 'current_exam' in st.session_state:
        take_exam()
        return
    
    choice = st.sidebar.radio("Menu", list(menu_options.keys()))
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
    
    # Display selected page
    menu_options[choice]()

if __name__ == "__main__":
    main()
