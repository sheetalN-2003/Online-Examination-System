import streamlit as st
from utils.db_operations import *
from firebase_config import db
from datetime import datetime, timedelta
import time
from typing import Dict, List

# Constants
DEFAULT_EXAM_DURATION = 30  # minutes
MAX_QUESTIONS = 50
MAX_OPTIONS = 5

def admin_dashboard():
    """Admin dashboard with enhanced analytics"""
    st.title("Admin Dashboard")
    
    # Real-time statistics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    users_count = len(get_all_users())
    exams_count = len(get_all_exams(active_only=False))
    active_exams = len(get_all_exams(active_only=True))
    results_count = len(get_leaderboard(limit=1000))  # Get all results
    
    col1.metric("Total Users", users_count)
    col2.metric("Total Exams", exams_count)
    col3.metric("Active Exams", active_exams)
    col4.metric("Exam Submissions", results_count)
    
    # Recent activity section
    st.subheader("Recent Activity")
    
    # Last 5 exam submissions
    try:
        recent_results = db.collection("results") \
                          .order_by("submitted_at", direction=firestore.Query.DESCENDING) \
                          .limit(5) \
                          .stream()
        
        st.write("**Latest Exam Submissions:**")
        for result in recent_results:
            result_data = result.to_dict()
            student = get_user(result_data['student_id'])
            exam = get_exam(result_data['exam_id'])
            
            if student and exam:
                st.write(f"- {student.get('full_name', student['email'])} scored {result_data['score']}/{result_data['max_score']} on {exam['name']} ({result_data['submitted_at'].strftime('%Y-%m-%d %H:%M')})")
    except Exception as e:
        st.error(f"Could not load recent activity: {str(e)}")

def manage_users():
    """Enhanced user management with search and filtering"""
    st.title("User Management")
    
    # Search and filter options
    col1, col2 = st.columns(2)
    search_term = col1.text_input("Search by name or email")
    role_filter = col2.selectbox("Filter by role", ["All", "student", "instructor", "admin"])
    
    # Get all users and apply filters
    users = get_all_users()
    
    if search_term:
        users = [u for u in users if search_term.lower() in u.get('email', '').lower() or 
                search_term.lower() in u.get('full_name', '').lower()]
    
    if role_filter != "All":
        users = [u for u in users if u.get('role') == role_filter]
    
    # Display user table with pagination
    if not users:
        st.info("No users found matching your criteria")
        return
    
    # Convert for display
    user_display = []
    for user in users:
        user_display.append({
            "Email": user['email'],
            "Name": user.get('full_name', 'N/A'),
            "Role": user.get('role', 'student').capitalize(),
            "Joined": user.get('created_at', 'N/A').strftime("%Y-%m-%d") if 'created_at' in user else 'N/A',
            "Last Login": user.get('last_login', 'N/A').strftime("%Y-%m-%d %H:%M") if 'last_login' in user else 'N/A'
        })
    
    st.dataframe(user_display, use_container_width=True)
    
    # User actions
    st.subheader("User Actions")
    selected_email = st.selectbox("Select user for actions", [u['email'] for u in users])
    
    if selected_email:
        selected_user = next(u for u in users if u['email'] == selected_email)
        current_role = selected_user.get('role', 'student')
        
        new_role = st.selectbox(
            "Change Role", 
            ["student", "instructor", "admin"],
            index=["student", "instructor", "admin"].index(current_role)
        )
        
        if st.button("Update Role") and new_role != current_role:
            try:
                db.collection('users').document(selected_user['uid']).update({'role': new_role})
                st.success(f"Role updated to {new_role}")
                time.sleep(1)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to update role: {str(e)}")

def manage_exams():
    """Enhanced exam management with more features"""
    st.title("Exam Management")
    
    tab1, tab2, tab3 = st.tabs(["Create Exam", "View/Edit Exams", "Exam Analytics"])
    
    with tab1:
        st.subheader("Create New Exam")
        
        with st.form("create_exam_form"):
            exam_name = st.text_input("Exam Name*", help="Required field")
            exam_duration = st.number_input(
                "Duration (minutes)*", 
                min_value=1, 
                max_value=180, 
                value=DEFAULT_EXAM_DURATION,
                help="Maximum 3 hours"
            )
            exam_description = st.text_area("Description")
            is_active = st.checkbox("Activate exam immediately", value=True)
            
            submitted = st.form_submit_button("Create Exam")
            
            if submitted:
                if not exam_name:
                    st.error("Exam name is required")
                else:
                    exam_data = {
                        'name': exam_name,
                        'duration': exam_duration,
                        'description': exam_description,
                        'created_by': st.session_state.user['uid'],
                        'is_active': is_active,
                        'created_at': datetime.now()
                    }
                    
                    try:
                        exam_id = create_exam(exam_data)
                        st.success(f"Exam created successfully! ID: {exam_id}")
                        time.sleep(1)
                        st.session_state.current_exam = exam_id
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to create exam: {str(e)}")
    
    with tab2:
        st.subheader("All Exams")
        
        # Filter options
        active_filter = st.selectbox("Filter by status", ["All", "Active Only", "Inactive Only"])
        
        # Get exams based on filter
        exams = get_all_exams(active_only=False)
        
        if active_filter == "Active Only":
            exams = [e for e in exams if e.get('is_active', False)]
        elif active_filter == "Inactive Only":
            exams = [e for e in exams if not e.get('is_active', True)]
        
        if not exams:
            st.info("No exams found matching your criteria")
        else:
            for exam in exams:
                with st.expander(f"{exam['name']} - {exam['duration']} mins ({'Active' if exam.get('is_active', False) else 'Inactive'})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(exam['description'])
                        st.caption(f"Created: {exam.get('created_at', 'N/A').strftime('%Y-%m-%d') if 'created_at' in exam else 'N/A'}")
                        st.caption(f"Total Questions: {exam.get('total_questions', 0)} | Total Points: {exam.get('total_points', 0)}")
                    
                    with col2:
                        # Toggle activation status
                        current_status = exam.get('is_active', False)
                        new_status = not current_status
                        
                        if st.button("Activate" if new_status else "Deactivate", key=f"toggle_{exam['id']}"):
                            try:
                                update_exam(exam['id'], {'is_active': new_status})
                                st.success(f"Exam {'activated' if new_status else 'deactivated'} successfully!")
                                time.sleep(1)
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Failed to update exam status: {str(e)}")
                        
                        if st.button("Manage Questions", key=f"manage_{exam['id']}"):
                            st.session_state.manage_exam_id = exam['id']
                            st.experimental_rerun()
    
    with tab3:
        st.subheader("Exam Analytics")
        
        exams = get_all_exams(active_only=False)
        if not exams:
            st.info("No exams available for analytics")
        else:
            selected_exam = st.selectbox("Select Exam", [e['name'] for e in exams], key="analytics_exam_select")
            
            if selected_exam:
                exam = next(e for e in exams if e['name'] == selected_exam)
                results = get_leaderboard(exam['id'], limit=1000)  # Get all results for this exam
                
                if not results:
                    st.info("No results available for this exam")
                else:
                    # Basic statistics
                    avg_score = sum(r['score'] for r in results) / len(results)
                    max_score = exam.get('total_points', 100)
                    pass_rate = sum(1 for r in results if r['score'] >= max_score * 0.6) / len(results) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Attempts", len(results))
                    col2.metric("Average Score", f"{avg_score:.1f}/{max_score}")
                    col3.metric("Pass Rate", f"{pass_rate:.1f}%")
                    
                    # Score distribution histogram
                    st.subheader("Score Distribution")
                    scores = [r['score'] for r in results]
                    st.bar_chart(scores)

def manage_questions(exam_id=None):
    """Enhanced question management with bulk operations"""
    if exam_id is None and 'manage_exam_id' not in st.session_state:
        st.error("No exam selected")
        return
    
    exam_id = exam_id or st.session_state.manage_exam_id
    exam = get_exam(exam_id)
    
    if not exam:
        st.error("Exam not found")
        return
    
    st.title(f"Manage Questions: {exam['name']}")
    
    tab1, tab2 = st.tabs(["Add Questions", "View/Edit Questions"])
    
    with tab1:
        st.subheader("Add New Question")
        
        question_type = st.selectbox("Question Type", ["Multiple Choice", "True/False", "Short Answer", "Essay"], key="q_type")
        
        with st.form("add_question_form"):
            question_text = st.text_area("Question Text*", height=100, help="Required field")
            points = st.number_input("Points*", min_value=1, max_value=10, value=1)
            question_number = st.number_input("Question Number", min_value=1, max_value=MAX_QUESTIONS, value=exam.get('total_questions', 0) + 1)
            
            options = []
            correct_answer = ""
            
            if question_type == "Multiple Choice":
                num_options = st.number_input("Number of options", min_value=2, max_value=MAX_OPTIONS, value=4)
                for i in range(num_options):
                    options.append(st.text_input(f"Option {i+1}*", key=f"option_{i}"))
                correct_answer = st.selectbox("Correct Answer*", options, key="mc_correct")
            elif question_type == "True/False":
                options = ["True", "False"]
                correct_answer = st.selectbox("Correct Answer*", options, key="tf_correct")
            elif question_type == "Short Answer":
                correct_answer = st.text_input("Correct Answer (Short Answer)*", key="sa_correct")
            else:  # Essay
                correct_answer = st.text_area("Sample Answer (for grading reference)", key="essay_sample")
            
            submitted = st.form_submit_button("Add Question")
            
            if submitted:
                if not question_text:
                    st.error("Question text is required")
                elif question_type == "Multiple Choice" and not all(options):
                    st.error("All options must be filled")
                else:
                    question_data = {
                        'text': question_text,
                        'type': question_type,
                        'options': options,
                        'correct_answer': correct_answer,
                        'points': points,
                        'question_number': question_number,
                        'created_at': datetime.now()
                    }
                    
                    try:
                        add_question_to_exam(exam_id, question_data)
                        st.success("Question added successfully!")
                        time.sleep(1)
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to add question: {str(e)}")
    
    with tab2:
        st.subheader("Existing Questions")
        
        questions = get_exam_questions(exam_id)
        if not questions:
            st.info("No questions added yet")
        else:
            # Sort by question number
            questions.sort(key=lambda x: x.get('question_number', 0))
            
            for i, question in enumerate(questions, 1):
                with st.expander(f"Q{question.get('question_number', i)}: {question['text']} ({question['points']} pts)"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Type:** {question['type']}")
                        
                        if question['type'] in ["Multiple Choice", "True/False"]:
                            st.write("**Options:**")
                            for opt in question['options']:
                                st.write(f"- {opt}")
                        
                        st.write(f"**Correct Answer:** {question['correct_answer']}")
                    
                    with col2:
                        if st.button("Delete", key=f"del_{question['id']}"):
                            try:
                                db.collection('exams').document(exam_id).collection('questions').document(question['id']).delete()
                                
                                # Update exam totals
                                db.collection('exams').document(exam_id).update({
                                    'total_questions': firestore.Increment(-1),
                                    'total_points': firestore.Increment(-question['points'])
                                })
                                
                                st.success("Question deleted successfully!")
                                time.sleep(1)
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Failed to delete question: {str(e)}")

def student_dashboard():
    """Enhanced student dashboard with progress tracking"""
    st.title("Student Dashboard")
    
    # Welcome message with progress stats
    user_data = get_user(st.session_state.user['uid'])
    exams_taken = user_data.get('exams_taken', 0)
    total_points = user_data.get('total_points', 0)
    
    col1, col2 = st.columns(2)
    col1.metric("Exams Taken", exams_taken)
    col2.metric("Total Points Earned", total_points)
    
    # Available exams
    st.subheader("Available Exams")
    exams = get_all_exams(active_only=True)
    
    if not exams:
        st.info("No active exams available at this time")
    else:
        for exam in exams:
            with st.expander(f"{exam['name']} - {exam['duration']} mins ({exam.get('total_questions', 0)} questions)"):
                st.write(exam['description'])
                st.caption(f"Total Points: {exam.get('total_points', 100)} | Passing Score: {exam.get('total_points', 100) * 0.6:.0f}+")
                
                # Check if student has already taken this exam
                results = db.collection("results") \
                          .where("student_id", "==", st.session_state.user['uid']) \
                          .where("exam_id", "==", exam['id']) \
                          .limit(1) \
                          .stream()
                
                has_taken = any(results)
                
                if has_taken:
                    st.warning("You've already taken this exam")
                    if st.button("View Results", key=f"results_{exam['id']}"):
                        st.session_state.view_exam_results = exam['id']
                        st.experimental_rerun()
                else:
                    if st.button("Take Exam", key=f"take_{exam['id']}"):
                        st.session_state.current_exam = exam
                        st.experimental_rerun()

def take_exam():
    """Enhanced exam taking interface with better UX"""
    if 'current_exam' not in st.session_state:
        st.warning("No exam selected. Please select an exam from the dashboard.")
        return
    
    exam = st.session_state.current_exam
    st.title(f"Exam: {exam['name']}")
    
    # Initialize session variables
    if 'exam_start_time' not in st.session_state:
        st.session_state.exam_start_time = time.time()
        st.session_state.answers = {}
    
    # Timer
    exam_duration = exam['duration'] * 60  # Convert to seconds
    elapsed_time = time.time() - st.session_state.exam_start_time
    remaining_time = max(0, exam_duration - elapsed_time)
    
    # Convert to minutes and seconds
    minutes, seconds = divmod(int(remaining_time), 60)
    time_display = f"{minutes:02d}:{seconds:02d}"
    
    # Progress bar
    progress = min(1.0, elapsed_time / exam_duration)
    st.progress(progress)
    
    # Time warning system
    if remaining_time <= 300:  # 5 minutes remaining
        st.error(f"Time remaining: {time_display} - Hurry up!")
    else:
        st.write(f"Time remaining: {time_display}")
    
    if remaining_time <= 0:
        st.error("Time's up! Your exam will be automatically submitted.")
        # Auto-submit logic would go here
        return
    
    # Get questions
    questions = get_exam_questions(exam['id'])
    questions.sort(key=lambda x: x.get('question_number', 0))
    
    # Exam instructions
    st.write(f"**Instructions:** Answer all {len(questions)} questions. Total points: {exam.get('total_points', 100)}")
    
    # Form for answers
    with st.form("exam_form"):
        for i, question in enumerate(questions, 1):
            st.subheader(f"Question {question.get('question_number', i)} ({question['points']} pts)")
            st.write(question['text'])
            
            # Store answers in session state
            answer_key = f"q_{question['id']}"
            
            if question['type'] == "Multiple Choice":
                st.session_state.answers[answer_key] = st.radio(
                    "Select your answer",
                    question['options'],
                    key=answer_key,
                    index=st.session_state.answers.get(answer_key, 0)
                )
            elif question['type'] == "True/False":
                st.session_state.answers[answer_key] = st.radio(
                    "Select your answer",
                    ["True", "False"],
                    key=answer_key,
                    index=st.session_state.answers.get(answer_key, 0)
                )
            elif question['type'] == "Short Answer":
                st.session_state.answers[answer_key] = st.text_input(
                    "Your answer",
                    key=answer_key,
                    value=st.session_state.answers.get(answer_key, ""))
            else:  # Essay
                st.session_state.answers[answer_key] = st.text_area(
                    "Your answer",
                    key=answer_key,
                    value=st.session_state.answers.get(answer_key, ""),
                    height=200)
            
            st.divider()
        
        # Submit button
        submitted = st.form_submit_button("Submit Exam")
        
        if submitted:
            # Calculate score
            score = 0
            max_score = sum(q['points'] for q in questions)
            
            for question in questions:
                answer_key = f"q_{question['id']}"
                user_answer = st.session_state.answers.get(answer_key, "")
                
                if user_answer == question['correct_answer']:
                    score += question['points']
            
            # Save results
            results = {
                'exam_id': exam['id'],
                'exam_name': exam['name'],
                'student_id': st.session_state.user['uid'],
                'student_name': st.session_state.user['display_name'],
                'score': score,
                'max_score': max_score,
                'answers': st.session_state.answers,
                'submitted_at': datetime.now(),
                'time_taken': elapsed_time
            }
            
            try:
                submit_exam_results(results)
                st.success(f"Exam submitted! Your score: {score}/{max_score}")
                
                # Clear exam state
                del st.session_state.current_exam
                del st.session_state.exam_start_time
                del st.session_state.answers
                
                time.sleep(2)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to submit exam: {str(e)}")

def view_student_results():
    """Enhanced results viewing with more details"""
    st.title("My Results")
    
    results = get_student_results(st.session_state.user['uid'])
    
    if not results:
        st.info("You haven't taken any exams yet.")
        return
    
    # Group results by exam
    exam_results = {}
    for result in results:
        if result['exam_name'] not in exam_results:
            exam_results[result['exam_name']] = []
        exam_results[result['exam_name']].append(result)
    
    # Display by exam with best attempt first
    for exam_name, attempts in exam_results.items():
        # Sort attempts by score (descending)
        attempts.sort(key=lambda x: x['score'], reverse=True)
        best_attempt = attempts[0]
        
        with st.expander(f"{exam_name} - Best: {best_attempt['score']}/{best_attempt['max_score']} ({len(attempts)} attempts)"):
            st.write(f"**Highest Score:** {best_attempt['score']}/{best_attempt['max_score']} ({best_attempt['score']/best_attempt['max_score']*100:.1f}%)")
            st.write(f"**First Attempt:** {attempts[-1]['submitted_at'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Latest Attempt:** {attempts[0]['submitted_at'].strftime('%Y-%m-%d %H:%M')}")
            
            if st.button("View Details", key=f"details_{exam_name}"):
                st.session_state.view_exam_results = attempts[0]['exam_id']
                st.experimental_rerun()

def view_leaderboard():
    """Enhanced leaderboard with more filtering options"""
    st.title("Leaderboard")
    
    exams = get_all_exams(active_only=False)
    exam_options = {exam['name']: exam['id'] for exam in exams}
    exam_options["All Exams"] = None
    
    col1, col2 = st.columns(2)
    selected_exam = col1.selectbox("Select Exam", list(exam_options.keys()))
    limit = col2.number_input("Top Results to Show", min_value=5, max_value=50, value=10)
    
    results = get_leaderboard(exam_options[selected_exam], limit=limit)
    
    if not results:
        st.info("No results available yet.")
        return
    
    # Enhanced display table
    leaderboard_data = []
    for i, result in enumerate(results, 1):
        leaderboard_data.append({
            "Rank": i,
            "Student": result['student_name'],
            "Exam": result['exam_name'],
            "Score": f"{result['score']}/{result['max_score']}",
            "Percentage": f"{result['percentage']:.1f}%",
            "Submitted": result['submitted_at'].strftime('%Y-%m-%d %H:%M')
        })
    
    st.dataframe(leaderboard_data, use_container_width=True, hide_index=True)
    
    # Visualizations
    if selected_exam != "All Exams" and len(results) > 1:
        st.subheader("Performance Distribution")
        
        # Convert percentage to float for chart
        percentages = [float(r['percentage']) for r in results]
        st.bar_chart(percentages)
