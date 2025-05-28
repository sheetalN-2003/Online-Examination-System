import streamlit as st
from utils.db_operations import *

def admin_dashboard():
    """Admin dashboard page"""
    st.title("Admin Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Statistics
    users_count = len(get_all_users())
    exams_count = len(get_all_exams())
    results_count = len(get_leaderboard())
    
    col1.metric("Total Users", users_count)
    col2.metric("Total Exams", exams_count)
    col3.metric("Total Results", results_count)
    
    # Recent activity
    st.subheader("Recent Activity")
    # Add recent activity visualization here

def manage_users():
    """User management page for admin"""
    st.title("User Management")
    
    # List all users
    users = get_all_users()
    st.table([{
        "Email": user['email'],
        "Name": user.get('full_name', 'N/A'),
        "Role": user.get('role', 'student'),
        "Joined": user.get('created_at', 'N/A').strftime("%Y-%m-%d") if 'created_at' in user else 'N/A'
    } for user in users])

def manage_exams():
    """Exam management page for admin"""
    st.title("Exam Management")
    
    tab1, tab2 = st.tabs(["Create Exam", "View Exams"])
    
    with tab1:
        st.subheader("Create New Exam")
        
        exam_name = st.text_input("Exam Name")
        exam_duration = st.number_input("Duration (minutes)", min_value=1, value=30)
        exam_description = st.text_area("Description")
        
        if st.button("Create Exam"):
            exam_data = {
                'name': exam_name,
                'duration': exam_duration,
                'description': exam_description,
                'created_by': st.session_state.user['uid']
            }
            create_exam(exam_data)
    
    with tab2:
        st.subheader("All Exams")
        exams = get_all_exams()
        
        for exam in exams:
            with st.expander(f"{exam['name']} - {exam['duration']} mins"):
                st.write(exam['description'])
                if st.button(f"Manage Questions", key=f"manage_{exam['id']}"):
                    manage_questions(exam['id'])

def manage_questions(exam_id):
    """Manage questions for a specific exam"""
    st.title("Manage Questions")
    
    # Get existing questions
    questions = get_exam_questions(exam_id)
    
    # Form to add new question
    st.subheader("Add New Question")
    question_text = st.text_area("Question Text")
    question_type = st.selectbox("Question Type", ["Multiple Choice", "True/False", "Short Answer"])
    
    options = []
    correct_answer = ""
    
    if question_type == "Multiple Choice":
        num_options = st.number_input("Number of options", min_value=2, max_value=5, value=4)
        for i in range(num_options):
            options.append(st.text_input(f"Option {i+1}"))
        correct_answer = st.selectbox("Correct Answer", options)
    elif question_type == "True/False":
        options = ["True", "False"]
        correct_answer = st.selectbox("Correct Answer", options)
    else:
        correct_answer = st.text_input("Correct Answer (Short Answer)")
    
    points = st.number_input("Points", min_value=1, value=1)
    
    if st.button("Add Question"):
        question_data = {
            'text': question_text,
            'type': question_type,
            'options': options,
            'correct_answer': correct_answer,
            'points': points
        }
        
        db_firestore.collection('exams').document(exam_id).collection('questions').add(question_data)
        st.success("Question added successfully!")
    
    # Display existing questions
    st.subheader("Existing Questions")
    for i, question in enumerate(questions, 1):
        with st.expander(f"Question {i}: {question['text']}"):
            st.write(f"Type: {question['type']}")
            st.write(f"Points: {question['points']}")
            if question['type'] in ["Multiple Choice", "True/False"]:
                st.write("Options:")
                for opt in question['options']:
                    st.write(f"- {opt}")
            st.write(f"Correct Answer: {question['correct_answer']}")

def view_results():
    """View all results (admin)"""
    st.title("Exam Results")
    
    exams = get_all_exams()
    exam_options = {exam['name']: exam['id'] for exam in exams}
    selected_exam = st.selectbox("Select Exam", list(exam_options.keys()))
    
    if selected_exam:
        results = get_leaderboard(exam_options[selected_exam])
        st.table([{
            "Student": result['student_name'],
            "Score": result['score'],
            "Submitted": result['submitted_at'].strftime("%Y-%m-%d %H:%M") if 'submitted_at' in result else 'N/A'
        } for result in results])

def student_dashboard():
    """Student dashboard page"""
    st.title("Student Dashboard")
    
    # Display upcoming exams
    st.subheader("Available Exams")
    exams = get_all_exams()
    
    for exam in exams:
        with st.expander(f"{exam['name']} - {exam['duration']} mins"):
            st.write(exam['description'])
            if st.button("Take Exam", key=f"take_{exam['id']}"):
                st.session_state.current_exam = exam
                st.experimental_rerun()

def take_exam():
    """Take exam page for students"""
    if 'current_exam' not in st.session_state:
        st.warning("No exam selected. Please select an exam from the dashboard.")
        return
    
    exam = st.session_state.current_exam
    st.title(f"Exam: {exam['name']}")
    
    # Timer
    exam_duration = exam['duration'] * 60  # Convert to seconds
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = max(0, exam_duration - elapsed_time)
    
    minutes, seconds = divmod(int(remaining_time), 60)
    st.write(f"Time remaining: {minutes:02d}:{seconds:02d}")
    
    if remaining_time <= 0:
        st.error("Time's up! Your exam will be automatically submitted.")
        # Auto-submit logic here
        return
    
    # Get questions
    questions = get_exam_questions(exam['id'])
    
    # Form for answers
    answers = {}
    for i, question in enumerate(questions, 1):
        st.subheader(f"Question {i}")
        st.write(question['text'])
        
        if question['type'] == "Multiple Choice":
            answers[f"q_{i}"] = st.radio(
                "Select your answer",
                question['options'],
                key=f"q_{i}"
            )
        elif question['type'] == "True/False":
            answers[f"q_{i}"] = st.radio(
                "Select your answer",
                ["True", "False"],
                key=f"q_{i}"
            )
        else:
            answers[f"q_{i}"] = st.text_input(
                "Your answer",
                key=f"q_{i}"
            )
    
    if st.button("Submit Exam"):
        # Calculate score
        score = 0
        max_score = sum(q['points'] for q in questions)
        
        for i, question in enumerate(questions, 1):
            if answers.get(f"q_{i}") == question['correct_answer']:
                score += question['points']
        
        # Save results
        results = {
            'exam_id': exam['id'],
            'exam_name': exam['name'],
            'student_id': st.session_state.user['uid'],
            'student_name': st.session_state.user['display_name'],
            'score': score,
            'max_score': max_score,
            'answers': answers,
            'submitted_at': datetime.now()
        }
        
        submit_exam_results(results)
        st.success(f"Exam submitted! Your score: {score}/{max_score}")
        time.sleep(2)
        del st.session_state.current_exam
        st.experimental_rerun()

def view_student_results():
    """View results for student"""
    st.title("My Results")
    
    results = get_student_results(st.session_state.user['uid'])
    
    if not results:
        st.info("You haven't taken any exams yet.")
        return
    
    for result in results:
        with st.expander(f"{result['exam_name']} - {result['score']}/{result['max_score']}"):
            st.write(f"Score: {result['score']}/{result['max_score']}")
            st.write(f"Submitted on: {result['submitted_at'].strftime('%Y-%m-%d %H:%M')}")

def view_leaderboard():
    """View leaderboard"""
    st.title("Leaderboard")
    
    exams = get_all_exams()
    exam_options = {exam['name']: exam['id'] for exam in exams}
    exam_options["All Exams"] = None
    selected_exam = st.selectbox("Select Exam", list(exam_options.keys()))
    
    results = get_leaderboard(exam_options[selected_exam])
    
    if not results:
        st.info("No results available yet.")
        return
    
    st.table([{
        "Rank": i+1,
        "Student": result['student_name'],
        "Exam": result['exam_name'],
        "Score": f"{result['score']}/{result['max_score']}",
        "Percentage": f"{round(result['score']/result['max_score']*100)}%"
    } for i, result in enumerate(results[:10])])  # Show top 10
