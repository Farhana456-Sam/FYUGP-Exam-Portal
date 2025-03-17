from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
from mcq import mcq_bp  # Import MCQ blueprint
from dashboard import dashboard_bp  # Import Dashboard blueprint
from subjective import subjective_bp  # Import Subjective blueprint
from login import faculty_bp  # Import Faculty login blueprint
from feedback import feedback_bp 
from coding_exam import coding_exam_bp

app = Flask(__name__)
app.secret_key = "secret_key"

# Load student dataset
csv_file = "Kerala_Students_Dataset.csv"

if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()  # Remove spaces in column names
    df["Login ID"] = df["Login ID"].astype(str)  # Convert Login ID to string
    df["Total_Score"] = pd.to_numeric(df["Total_Score"], errors="coerce")  # Ensure scores are numeric
else:
    df = pd.DataFrame(columns=["Login ID", "Full Name", "Department", "Total_Score"])
    print("Error: Kerala_Students_Dataset.csv not found!")

# Register Blueprints
app.register_blueprint(mcq_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(subjective_bp)
app.register_blueprint(faculty_bp)  # Registering faculty login blueprint
app.register_blueprint(feedback_bp)  # Registering feedback blueprint
app.register_blueprint(coding_exam_bp)

# ------------------ HOME ROUTE ------------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    login_id = request.form.get("loginId")

    if not login_id:
        return render_template("login.html", error="Login ID is required.")

    student = df[df["Login ID"] == login_id]

    if not student.empty:
        student_name = student.iloc[0]["Full Name"]
        department = student.iloc[0]["Department"]
        total_marks = student.iloc[0]["Total_Score"]
        
        session["user"] = login_id
        session["student_name"] = student_name
        session["department"] = department
        session["total_marks"] = total_marks
        session["QuestionID"] = 0  

        return redirect(url_for("dashboard.dashboard", login_id=login_id, student_name=student_name, department=department, total_marks=total_marks))
    else:
        return render_template("login.html", error="Invalid Login ID")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
