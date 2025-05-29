from firebase_config import db
from datetime import datetime
from typing import List, Dict, Optional

def create_exam(exam_data: Dict) -> str:
    """Create a new exam in Firestore"""
    try:
        exam_ref = db.collection("exams").document()
        exam_data.update({
            "created_at": datetime.now(),
            "is_active": True,
            "total_questions": 0,
            "total_points": 0
        })
        exam_ref.set(exam_data)
        return exam_ref.id
    except Exception as e:
        raise Exception(f"Failed to create exam: {str(e)}")

def get_exam(exam_id: str) -> Dict:
    """Fetch exam details"""
    try:
        exam = db.collection("exams").document(exam_id).get()
        if exam.exists:
            return exam.to_dict()
        return None
    except Exception as e:
        raise Exception(f"Failed to get exam: {str(e)}")

def get_all_exams(active_only: bool = True) -> List[Dict]:
    """Get all exams, optionally filtered by active status"""
    try:
        query = db.collection("exams")
        if active_only:
            query = query.where("is_active", "==", True)
        exams = query.stream()
        return [{"id": exam.id, **exam.to_dict()} for exam in exams]
    except Exception as e:
        raise Exception(f"Failed to get exams: {str(e)}")

def update_exam(exam_id: str, update_data: Dict) -> None:
    """Update exam details"""
    try:
        db.collection("exams").document(exam_id).update(update_data)
    except Exception as e:
        raise Exception(f"Failed to update exam: {str(e)}")

def add_question_to_exam(exam_id: str, question_data: Dict) -> str:
    """Add a question to an exam"""
    try:
        # Add question to subcollection
        question_ref = db.collection("exams").document(exam_id).collection("questions").document()
        question_data.update({
            "created_at": datetime.now(),
            "question_number": question_data.get("question_number", 0)
        })
        question_ref.set(question_data)
        
        # Update exam totals
        exam_ref = db.collection("exams").document(exam_id)
        exam_ref.update({
            "total_questions": firestore.Increment(1),
            "total_points": firestore.Increment(question_data.get("points", 1))
        })
        
        return question_ref.id
    except Exception as e:
        raise Exception(f"Failed to add question: {str(e)}")

def get_exam_questions(exam_id: str) -> List[Dict]:
    """Get all questions for an exam"""
    try:
        questions = db.collection("exams").document(exam_id).collection("questions").order_by("question_number").stream()
        return [{"id": q.id, **q.to_dict()} for q in questions]
    except Exception as e:
        raise Exception(f"Failed to get questions: {str(e)}")

def submit_exam_results(result_data: Dict) -> str:
    """Save exam results"""
    try:
        result_ref = db.collection("results").document()
        result_data.update({
            "submitted_at": datetime.now(),
            "percentage": (result_data["score"] / result_data["max_score"]) * 100
        })
        result_ref.set(result_data)
        
        # Update user's exam history
        user_ref = db.collection("users").document(result_data["student_id"])
        user_ref.update({
            "exams_taken": firestore.Increment(1),
            "total_points": firestore.Increment(result_data["score"]),
            "last_exam_taken": datetime.now()
        })
        
        return result_ref.id
    except Exception as e:
        raise Exception(f"Failed to submit results: {str(e)}")

def get_student_results(student_id: str) -> List[Dict]:
    """Get all results for a student"""
    try:
        results = db.collection("results").where("student_id", "==", student_id).order_by("submitted_at", direction=firestore.Query.DESCENDING).stream()
        return [{"id": r.id, **r.to_dict()} for r in results]
    except Exception as e:
        raise Exception(f"Failed to get student results: {str(e)}")

def get_leaderboard(exam_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Get top results, optionally filtered by exam"""
    try:
        query = db.collection("results")
        if exam_id:
            query = query.where("exam_id", "==", exam_id)
        results = query.order_by("percentage", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        # Enhance results with additional data
        enhanced_results = []
        for result in results:
            result_data = result.to_dict()
            # Get student name
            student = db.collection("users").document(result_data["student_id"]).get()
            if student.exists:
                result_data["student_name"] = student.get("full_name") or student.get("email").split("@")[0]
            enhanced_results.append({"id": result.id, **result_data})
        
        return enhanced_results
    except Exception as e:
        raise Exception(f"Failed to get leaderboard: {str(e)}")

def get_all_users() -> List[Dict]:
    """Get all users from Firestore"""
    try:
        users = db.collection("users").stream()
        return [{"id": u.id, **u.to_dict()} for u in users]
    except Exception as e:
        raise Exception(f"Failed to get users: {str(e)}")

def get_user(user_id: str) -> Dict:
    """Get a single user's data"""
    try:
        user = db.collection("users").document(user_id).get()
        if user.exists:
            return user.to_dict()
        return None
    except Exception as e:
        raise Exception(f"Failed to get user: {str(e)}")
