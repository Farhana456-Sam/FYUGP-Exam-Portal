from flask import Blueprint, render_template, request, redirect, session, url_for, send_file, flash  
import pandas as pd
import os

mcq_bp = Blueprint("mcq", __name__)

# Load MCQ dataset
mcq_file = "MCQ test.csv"
result_file = "result.csv"

if os.path.exists(mcq_file):
    mcqs_df = pd.read_csv(mcq_file)
    mcqs_df.columns = mcqs_df.columns.str.strip()  # Remove spaces from column names
    print(f"DEBUG: Total Questions in Dataset = {len(mcqs_df)}")  # Debugging output
else:
    print("Error: MCQ_test.csv not found!")
    mcqs_df = pd.DataFrame(columns=["Question", "OptionA", "OptionB", "OptionC", "OptionD", "Correct Answer"])

# Function to check if the student has already attended the exam
def has_already_attended_exam(login_id):
    """Check if the student has already taken the exam by looking at the result file."""
    if os.path.exists(result_file):
        result_df = pd.read_csv(result_file, dtype=str)  # Ensure strings are read correctly
        if "Login ID" in result_df.columns:
            return login_id in result_df["Login ID"].values  # Check if student ID exists
    return False

def evaluate_responses(mcqs_df, responses):
    """Evaluate student answers and calculate score, percentage, and grade."""
    score = 0
    total_questions = len(mcqs_df)

    for index, row in mcqs_df.iterrows():
        correct_answer = row["Correct Answer"].strip().upper()
        student_answer = responses.get(str(index), "").strip().upper()

        if student_answer == correct_answer:
            score += 1

    percentage = (score / total_questions) * 100
    grade = assign_grade(percentage)
    return score, total_questions, percentage, grade

def assign_grade(percentage):
    """Assign grade based on percentage."""
    if percentage >= 90:
        return 'A'
    elif percentage >= 75:
        return 'B'
    elif percentage >= 50:
        return 'C'
    else:
        return 'D'

@mcq_bp.route("/mcq")
def mcq():
    """Load the first question or redirect if exam is completed."""
    if "user" not in session:
        return redirect(url_for("home"))

    login_id = session.get("user")

    # If student already attended, prevent retake
    if has_already_attended_exam(login_id):
        session["exam_completed"] = True
        flash("You have already attended the exam. Thank you.", "error")
        return redirect(url_for('dashboard.dashboard', 
                                login_id=session.get('user', ''), 
                                student_name=session.get('student_name', ''), 
                                department=session.get('department', ''), 
                                total_marks=session.get('total_marks', 0)))

    question_index = session.get("QuestionID", 0)
    questions = mcqs_df.to_dict(orient="records")

    if question_index >= len(questions):
        return redirect(url_for("mcq.submit_mcq"))

    question = questions[question_index]
    return render_template("mcq_test.html", question=question, question_index=question_index, total=len(questions), total_marks=session.get("total_marks", 0))

@mcq_bp.route("/mcq/next", methods=["POST"])
def next_mcq():
    """Store the student's answer and move to the next question."""
    if "user" not in session:
        return redirect(url_for("home"))

    user_answer = request.form.get("answer", "").strip().upper()
    question_index = session.get("QuestionID", 0)

    # Store responses in session
    responses = session.get("responses", {})
    responses[str(question_index)] = user_answer
    session["responses"] = responses  # Update session

    if question_index + 1 < len(mcqs_df):
        session["QuestionID"] = question_index + 1
        session.modified = True  # Ensure session is saved
        print(f"DEBUG: Current Question Index = {question_index}, Moving to: {session['QuestionID']}")  # Debugging output
        return redirect(url_for("mcq.mcq"))
    else:
        return redirect(url_for("mcq.submit_mcq"))

@mcq_bp.route("/mcq/submit", methods=["GET", "POST"])
def submit_mcq():
    """Process exam submission and generate a downloadable result file."""
    if "user" not in session:
        return redirect(url_for("home"))

    if session.get("exam_completed", False):
        flash("You have already submitted the exam.", "error")
        return redirect(url_for("dashboard.dashboard", login_id=session.get("user"), student_name=session.get("student_name"), department=session.get("department"), total_marks=session.get("total_marks", 0)))
    responses = session.get("responses", {})
    score, total_questions, percentage, grade = evaluate_responses(mcqs_df, responses)

    # Fetch student details
    login_id = session.get("user", "Unknown_ID")
    student_name = session.get("student_name", "Unknown")
    department = session.get("department", "Unknown")
    
    # Mark the exam as completed
    session["exam_completed"] = True  

    # Save results to a downloadable file
    filename = f"{login_id}_result.csv"
    file_path = os.path.join("static", filename)

    result_data = pd.DataFrame([{ "Login ID": login_id, "Student Name": student_name, "Department": department,
                                  "Total Marks": score, "Total Questions": total_questions,
                                  "Percentage": percentage, "Grade": grade }])
    result_data.to_csv(file_path, index=False)

    # Append results to faculty CSV file
    if not os.path.exists(result_file):
        result_data.to_csv(result_file, index=False, mode='w', header=True)
    else:
        result_data.to_csv(result_file, index=False, mode='a', header=False)
    
    flash("Exam submitted successfully! Download your result below.", "success")
    return redirect(url_for("mcq.download_result"))
    
@mcq_bp.route("/mcq/download_result")
def download_result():
    """Allow the student to download their result file."""
    if "user" not in session:
        return redirect(url_for("home"))

    login_id = session.get("user", "Unknown_ID")
    filename = f"{login_id}_result.csv"
    file_path = os.path.join("static", filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("Result file not found. Please contact support.", "error")
        return redirect(url_for("dashboard.dashboard", login_id=session.get("user"), student_name=session.get("student_name"), department=session.get("department"), total_marks=session.get("total_marks", 0)))

@mcq_bp.route("/mcq/show_responses")
def show_responses():
    """Show stored responses for debugging."""
    return str(session.get("responses", {}))
