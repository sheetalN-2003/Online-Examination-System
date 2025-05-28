import firebase_admin
from firebase_admin import credentials, auth, db, firestore

# Initialize Firebase (replace with your config)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-project.firebaseio.com',
    'storageBucket': 'your-project.appspot.com'
})

# Get Firestore client
db_firestore = firestore.client()
