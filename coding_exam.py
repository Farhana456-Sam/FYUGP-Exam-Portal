from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import csv
import os
import subprocess
import pandas as pd

# Define Blueprint
coding_exam_bp = Blueprint('coding_exam', __name__)

# File paths
QUESTIONS_FILE = "code.csv"
RESULTS_FILE = "coding_exam_results.csv"

# Ensure results file exists with correct headers
if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Login ID", "Student Name", "Department", "Total Marks", "Grade", "Percentage"])

# Load questions from CSV
try:
    df_questions = pd.read_csv(QUESTIONS_FILE, encoding="utf-8").dropna(subset=["Instruction", "Input", "Output"])
except (pd.errors.ParserError, FileNotFoundError):
    print("Error: The CSV file is missing or has incorrect format. Please check the file.")
    df_questions = pd.DataFrame(columns=["Instruction", "Input", "Output"])  # Empty DataFrame as fallback

@coding_exam_bp.route('/coding-exam', methods=['GET', 'POST'])
def coding_exam():
    if "user" not in session:
        return redirect(url_for("login"))

    if "question_index" not in session:
        session["question_index"] = 0
        session["total_marks"] = 0  # Reset total marks at the start

    question_index = session["question_index"]

    if question_index >= len(df_questions):
        return redirect(url_for("coding_exam.results"))

    question_row = df_questions.iloc[question_index]
    question = str(question_row["Instruction"]).strip()
    expected_output = str(question_row["Output"]).strip()
    input_data = str(question_row["Input"]).strip()

    if request.method == 'POST':
        student_code = request.form.get("code", "").strip()

        try:
            process = subprocess.run(
                ["python", "-c", student_code],
                input=input_data, text=True,
                capture_output=True, timeout=5
            )
            output = process.stdout.strip()
        except subprocess.TimeoutExpired:
            output = "Error: Code execution timed out."
        except Exception as e:
            output = f"Error: {str(e)}"

        # Assign marks based on output correctness
        marks = 5 if output.casefold() == expected_output.casefold() else 0
        session["total_marks"] += marks
        session.modified = True

        session["question_index"] += 1

        if session["question_index"] >= len(df_questions):
            return redirect(url_for("coding_exam.results"))

        return redirect(url_for("coding_exam.coding_exam"))

    return render_template("coding_exam.html", 
                           question=question, 
                           is_last_question=(question_index == len(df_questions) - 1))

@coding_exam_bp.route('/coding-exam/results')
def results():
    if "total_marks" not in session:
        flash("No results found. Please complete the exam.")
        return redirect(url_for("coding_exam.coding_exam"))

    total_marks = session.pop("total_marks", 0)
    total_questions = len(df_questions)
    
    # Avoid division by zero
    percentage = (total_marks / (total_questions * 5) * 100) if total_questions > 0 else 0

    # Assign grade based on percentage
    if percentage >= 90:
        grade = "A"
    elif percentage >= 75:
        grade = "B"
    elif percentage >= 50:
        grade = "C"
    elif percentage >= 35:
        grade = "D"
    else:
        grade = "F"

    login_id = session.get("user", "Unknown")
    student_name = session.get("student_name", "Unknown")
    department = session.get("department", "Unknown")

    # Save result to CSV file
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([login_id, student_name, department, total_marks, grade, round(percentage, 2)])

    return render_template("coding_exam_results.html", 
                           login_id=login_id, 
                           student_name=student_name, 
                           department=department,
                           total_marks=total_marks, 
                           grade=grade, 
                           percentage=round(percentage, 2))
