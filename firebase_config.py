import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variable to track initialization
_firebase_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK with environment variables"""
    global _firebase_initialized
    
    # Return existing client if already initialized
    if _firebase_initialized:
        return firestore.client()

    try:
        # Configuration using environment variables
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        }

        # Validate required environment variables
        required_vars = ["FIREBASE_PROJECT_ID", "FIREBASE_PRIVATE_KEY", "FIREBASE_CLIENT_EMAIL"]
        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Missing required environment variable: {var}")

        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv("FIREBASE_DATABASE_URL"),
                'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
            })
            _firebase_initialized = True

        return firestore.client()

    except ValueError as ve:
        print(f"Configuration error: {ve}")
        return None
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return None

# Initialize Firebase and get Firestore client
db_firestore = initialize_firebase()

# Verification function to check initialization
def is_firebase_initialized():
    """Check if Firebase was successfully initialized"""
    try:
        auth = firebase_admin.auth
        return True
    except:
        return False
