from firebase_config import db
from datetime import datetime

def create_exam(exam_data):
    """Create a new exam in Firestore"""
    exam_ref = db.collection("exams").document()
    exam_ref.set({
        **exam_data,
        "created_at": datetime.now()
    })
    return exam_ref.id

def get_exam(exam_id):
    """Fetch exam details"""
    return db.collection("exams").document(exam_id).get().to_dict()

def submit_result(student_id, exam_id, score):
    """Save exam results"""
    db.collection("results").add({
        "student_id": student_id,
        "exam_id": exam_id,
        "score": score,
        "submitted_at": datetime.now()
    })

def get_leaderboard(exam_id=None):
    """Get top 10 results"""
    query = db.collection("results")
    if exam_id:
        query = query.where("exam_id", "==", exam_id)
    return query.order_by("score", direction=firestore.Query.DESCENDING).limit(10).stream()
