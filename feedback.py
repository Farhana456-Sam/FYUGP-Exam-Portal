from flask import Blueprint, render_template, request, redirect, url_for, session
import csv
import os

feedback_bp = Blueprint('feedback', __name__)

# Ensure feedback file exists
FEEDBACK_FILE = "feedback.csv"
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Login ID", "Student Name", "MCQ Rating", "Subjective Rating", "Coding Rating", "Comments"])

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        login_id = session.get("user", "Unknown")  # Get student login ID from session
        student_name = session.get("student_name", "Unknown")  # Get student name from session
        mcq_rating = request.form.get('mcq-rating')
        subjective_rating = request.form.get('subjective-rating')
        coding_rating = request.form.get('coding-rating')
        comments = request.form.get('comments', '').strip()

        # Save feedback data in CSV file
        with open(FEEDBACK_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([login_id, student_name, mcq_rating, subjective_rating, coding_rating, comments])

        return redirect(url_for("dashboard.dashboard", login_id=session.get("user"), student_name=session.get("student_name"), department=session.get("department"), total_marks=session.get("total_marks", 0)))
    
    return render_template('feedback.html')
