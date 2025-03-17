from flask import Flask, Blueprint, request, send_file, flash, render_template, session, redirect, url_for
import torch
import pandas as pd
import os
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity

subjective_bp = Blueprint("subjective", __name__)

df = pd.read_csv("Subjective_Ques.csv")  # Ensure CSV has 'Question', 'Keyword 1', 'Keyword 2', etc.

# Load BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

RESULTS_FILE = "subjective_result.csv"
if not os.path.exists(RESULTS_FILE):
    pd.DataFrame(columns=["Student ID", "Answers", "Total Marks", "Grade"]).to_csv(RESULTS_FILE, index=False)

responses = {}  # Store student responses

def get_bert_embedding(text):
    """Generates BERT embedding for the given text."""
    text = text.lower().strip()
    if not text:
        return torch.zeros((1, 768))  # Return zero tensor for empty text
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)  # Average pooling

def count_keywords(student_answer, keyword_list):
    """Counts the number of keywords present in the student's answer."""
    student_answer = student_answer.lower().strip()
    return sum(1 for keyword in keyword_list if keyword.lower().strip() in student_answer)

def calculate_keyword_similarity(student_answer, keyword_list):
    """Counts the number of matched keywords in the student's answer."""
    if not keyword_list or not student_answer.strip():
        return 0  # No keywords or empty answer should give a minimum score

    matched_keywords = count_keywords(student_answer, keyword_list)  # Count exact keyword matches
    return matched_keywords  # Return count instead of a percentage

def assign_marks(matched_keywords):
    """Assign marks based on the number of matched keywords."""
    if matched_keywords >= 4:
        return 10
    elif matched_keywords == 3:
        return 8
    elif matched_keywords == 2:
        return 6
    elif matched_keywords == 1:
        return 4
    else:
        return 2  # Minimum marks for attempting the answer

def assign_grade(marks):
    """Assign grades based on total marks."""
    return 'A+' if marks >= 90 else 'A' if marks >= 80 else 'B' if marks >= 70 else 'C' if marks >= 60 else 'F'

@subjective_bp.route('/exam', methods=['GET', 'POST'])
def attend_exam():
    """Allow students to answer questions one time only."""
    if 'user' not in session:
        return redirect(url_for('home'))

    student_id = session['user']
    
    # Check if the student has already taken the exam
    result_df = pd.read_csv(RESULTS_FILE)
    if student_id in result_df["Student ID"].values:
        session["exam_completed"] = True
        return render_template("subjective_exam.html")

    session["exam_completed"] = False  # Reset if they haven't taken the exam

    if 'Question' not in df.columns:
        return "Error: Questions not found in dataset!", 500

    questions = df["Question"].tolist()
    question_index = session.get("QuestionID", 0)

    if request.method == 'POST':
        answer = request.form.get("answer", "").strip()
        if student_id not in responses:
            responses[student_id] = []
        responses[student_id].append(answer)
        question_index += 1
        session["QuestionID"] = question_index
        if question_index >= len(questions):
            return redirect(url_for("subjective.evaluate_exam"))
        return redirect(url_for("subjective.attend_exam"))

    return render_template("subjective_exam.html", questions=questions, question_index=question_index, total=len(questions))


@subjective_bp.route("/evaluate", methods=["GET"])
def evaluate_exam():
    """Evaluate student responses using keyword matching."""
    if 'user' not in session:
        return redirect(url_for('home'))

    student_id = session['user']
    student_responses = responses.get(student_id, [])

    if 'Question' not in df.columns or not any(col.startswith("Keyword") for col in df.columns):
        return "Error: Questions or Keywords not found in dataset!", 500

    questions = df["Question"].tolist()
    keyword_columns = [col for col in df.columns if col.startswith("Keyword")]
    correct_keywords = df[keyword_columns].values.tolist()

    if len(student_responses) != len(questions):
        return "Error: Mismatch in questions and responses!", 500

    total_marks = 0
    results = []

    for i, student_ans in enumerate(student_responses):
        matched_keywords = calculate_keyword_similarity(student_ans, correct_keywords[i])
        marks = assign_marks(matched_keywords)  # Assign marks correctly
        total_marks += marks
        results.append((i + 1, marks, float(matched_keywords)))  # Ensure it's a float

    grade = assign_grade(total_marks)
    session["total_marks"] = total_marks
    session["grade"] = grade

    # Save result to CSV
    result_df = pd.read_csv(RESULTS_FILE)
    new_result = pd.DataFrame([[student_id, responses[student_id], total_marks, grade]],
                              columns=["Student ID", "Answers", "Total Marks", "Grade"])
    result_df = pd.concat([result_df, new_result], ignore_index=True)
    result_df.to_csv(RESULTS_FILE, index=False)

    return render_template("evaluation_result.html", student_id=student_id, total_marks=total_marks, grade=grade, results=results)

@subjective_bp.route("/download_result")
def download_result():
    """Allow the student to download their result file."""
    if "user" not in session:
        return redirect(url_for("home"))

    login_id = session.get("user", "Unknown_ID")
    filename = f"{login_id}_subjective_result.csv"
    file_path = os.path.join("static", filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("Result file not found. Please contact support.", "error")
        return redirect(url_for("dashboard.dashboard", login_id=session.get("user"), student_name=session.get("student_name"), department=session.get("department"), total_marks=session.get("total_marks", 0)))
