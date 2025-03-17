import csv
import os
from flask import Blueprint, request, render_template, session, redirect, url_for, flash

faculty_bp = Blueprint("faculty_bp", __name__)  # Define Blueprint

FACULTY_DATASET = "faculty_dataset.csv"
MCQ_QUESTIONS_FILE = "mcq_questions.csv"
SUBJECTIVE_QUESTIONS_FILE = "subjective_questions.csv"
MCQ_RESULTS_FILE = "result.csv"
SUBJECTIVE_RESULTS_FILE = "subjective_result.csv"
CODING_RESULTS_FILE = "coding_exam_results.csv"
FEEDBACK_FILE = "feedback.csv"

# Load faculty credentials
# Load faculty credentials
def load_faculty():
    faculty = {}  # Ensure faculty is always a dictionary
    if not os.path.exists(FACULTY_DATASET):
        print("Warning: Faculty dataset not found!")
        return faculty  # Return empty dictionary instead of None

    with open(FACULTY_DATASET, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            faculty[row["Login ID"]] = {"Password": row["Password"], "Faculty Name": row.get("Faculty Name", "Faculty")}

    return faculty  # Ensure function always returns a dictionary



@faculty_bp.route("/faculty_login", methods=["GET", "POST"])
def faculty_login():
    faculty = load_faculty()

    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        if login_id in faculty and faculty[login_id]["Password"] == password:
            session["login_id"] = login_id
            session["name"] = faculty[login_id].get("Faculty Name", "Faculty")
            return redirect(url_for("faculty_bp.faculty_dashboard"))

        flash("Invalid credentials, try again.", "error")

    return render_template("faculty_login.html")


@faculty_bp.route("/dashboard")
def faculty_dashboard():
    if "login_id" not in session:
        return redirect(url_for("faculty_bp.faculty_login"))
    return render_template("faculty_dashboard.html", name=session.get("name"))


@faculty_bp.route("/add_mcq", methods=["GET", "POST"])
def add_mcq():
    if "login_id" not in session:
        return redirect(url_for("faculty_bp.faculty_login"))

    if request.method == "POST":
        question = request.form.get("question")
        options = [request.form.get(f"option{opt}") for opt in "ABCD"]
        correct_answer = request.form.get("correct_answer")

        if not question or not all(options) or not correct_answer:
            flash("All fields are required!", "error")
            return redirect(url_for("faculty_bp.add_mcq"))

        file_exists = os.path.exists(MCQ_QUESTIONS_FILE)

        with open(MCQ_QUESTIONS_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Question", "Option A", "Option B", "Option C", "Option D", "Correct Answer"])
            writer.writerow([question] + options + [correct_answer])

        flash("MCQ question added successfully!", "success")
        return redirect(url_for("faculty_bp.faculty_dashboard"))

    return render_template("add_mcq.html")


@faculty_bp.route("/add_subjective", methods=["GET", "POST"])
def add_subjective():
    if "login_id" not in session:
        return redirect(url_for("faculty_bp.faculty_login"))

    if request.method == "POST":
        question = request.form.get("question")
        keywords = [request.form.get(f"keyword{i}") for i in range(1, 5)]

        if not question or not any(keywords):
            flash("Please provide at least one keyword!", "error")
            return redirect(url_for("faculty_bp.add_subjective"))

        file_exists = os.path.exists(SUBJECTIVE_QUESTIONS_FILE)

        with open(SUBJECTIVE_QUESTIONS_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Question", "Keyword1", "Keyword2", "Keyword3", "Keyword4"])
            writer.writerow([question] + keywords)

        flash("Subjective question added successfully!", "success")
        return redirect(url_for("faculty_bp.faculty_dashboard"))

    return render_template("add_subjective.html")


@faculty_bp.route("/view_results/<exam_type>")
def view_results(exam_type):
    if "login_id" not in session:
        return redirect(url_for("faculty_bp.faculty_login"))

    file_map = {
        "mcq": MCQ_RESULTS_FILE,
        "subjective": SUBJECTIVE_RESULTS_FILE,
        "coding": CODING_RESULTS_FILE,
        "feedback": FEEDBACK_FILE,
    }

    file_path = file_map.get(exam_type)
    results = []

    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            results = list(reader)

    return render_template("view_results.html", results=results, exam_type=exam_type)


@faculty_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))