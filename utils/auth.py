import streamlit as st
from firebase_config import db, auth
import time
from datetime import datetime
import hashlib

def hash_password(password):
    """Simple password hashing for demonstration"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    """Login page for existing users"""
    st.title("Login to Online Exam System")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if not email or not password:
            st.error("Please fill in all fields")
            return
            
        try:
            # Get user from Firebase Auth
            user = auth.get_user_by_email(email)
            
            # In a real app, verify password properly (this is simplified)
            # Here we would normally verify the password with Firebase Auth
            # For now, we'll just check if the user exists
            
            # Get additional user data from Firestore
            user_data = db.collection('users').document(user.uid).get().to_dict()
            
            if not user_data:
                st.error("User data not found")
                return
                
            st.session_state.user = {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name or user.email.split('@')[0],
                'role': user_data.get('role', 'student')
            }
            
            st.success("Login successful!")
            time.sleep(1)
            st.experimental_rerun()
            
        except auth.UserNotFoundError:
            st.error("User not found. Please check your email or sign up.")
        except Exception as e:
            st.error(f"Login failed: {str(e)}")

def signup_page():
    """Signup page for new users"""
    st.title("Create New Account")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    full_name = st.text_input("Full Name")
    role = st.selectbox("Role", ["student", "instructor", "admin"])
    
    if st.button("Sign Up"):
        if not all([email, password, confirm_password, full_name]):
            st.error("Please fill in all fields")
            return
            
        if password != confirm_password:
            st.error("Passwords don't match")
            return
            
        if len(password) < 6:
            st.error("Password must be at least 6 characters")
            return
            
        try:
            # Create user in Firebase Auth
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
                'created_at': datetime.now(),
                'last_login': datetime.now()
            }
            
            db.collection('users').document(user.uid).set(user_data)
            
            st.success("Account created successfully! Please login.")
            time.sleep(2)
            st.experimental_rerun()
            
        except auth.EmailAlreadyExistsError:
            st.error("Email already exists. Please login instead.")
        except Exception as e:
            st.error(f"Signup failed: {str(e)}")

def forgot_password_page():
    """Password reset page"""
    st.title("Reset Password")
    
    email = st.text_input("Enter your email")
    
    if st.button("Send Reset Link"):
        if not email:
            st.error("Please enter your email")
            return
            
        try:
            # In a real app, we would send a password reset email
            # This is a simulation
            st.success(f"Password reset link sent to {email} (simulated)")
            
            # Log this action
            db.collection('password_resets').add({
                'email': email,
                'requested_at': datetime.now(),
                'ip': st.experimental_get_query_params().get('ip', [''])[0]
            })
            
        except Exception as e:
            st.error(f"Failed to send reset link: {str(e)}")

def logout():
    """Logout the current user"""
    if 'user' in st.session_state:
        # Update last login time before logging out
        db.collection('users').document(st.session_state.user['uid']).update({
            'last_login': datetime.now()
        })
        del st.session_state.user
    st.experimental_rerun()
