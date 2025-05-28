import streamlit as st
import firebase_admin
from firebase_admin import auth
import time

def login_page():
    """Login page for existing users"""
    st.title("Login to Online Exam System")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        try:
            user = auth.get_user_by_email(email)
            # In a real app, you would verify the password here
            # This is a simplified version
            st.session_state.user = {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name or user.email
            }
            
            # Check user role (simplified - in real app, get from Firestore)
            if user.email.endswith('@admin.com'):
                st.session_state.user_role = "admin"
            else:
                st.session_state.user_role = "student"
            
            st.success("Login successful!")
            time.sleep(1)
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def signup_page():
    """Signup page for new users"""
    st.title("Create New Account")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    full_name = st.text_input("Full Name")
    role = st.selectbox("Role", ["student", "instructor"])
    
    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("Passwords don't match")
            return
            
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=full_name
            )
            
            # Store additional user data in Firestore
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'full_name': full_name,
                'role': role,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            db_firestore.collection('users').document(user.uid).set(user_data)
            
            st.success("Account created successfully! Please login.")
            time.sleep(2)
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Signup failed: {e}")

def forgot_password_page():
    """Password reset page"""
    st.title("Reset Password")
    
    email = st.text_input("Enter your email")
    
    if st.button("Send Reset Link"):
        try:
            # In a real app, send password reset email
            st.success(f"Password reset link sent to {email} (simulated)")
        except Exception as e:
            st.error(f"Failed to send reset link: {e}")
