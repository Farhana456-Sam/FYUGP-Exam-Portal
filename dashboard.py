from flask import Blueprint, render_template
import matplotlib.pyplot as plt
import os

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/<login_id>/<student_name>/<department>/<total_marks>")
def dashboard(login_id, student_name, department, total_marks):
    total_marks = float(total_marks)
    remaining_marks = 400 - total_marks  # Fixed total marks

    # Generate pie chart
    labels = ["Obtained Marks", "Remaining Marks"]
    values = [total_marks, remaining_marks]
    colors = ["#1E88E5", "#B0BEC5"]

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140)
    plt.title(f"Marks Distribution for {student_name}", fontsize=14)

    # Save the chart image
    chart_path = f"static/{login_id}_pie_chart.png"
    plt.savefig(chart_path)
    plt.close()

    return render_template(
        "dashboard.html",
        login_id=login_id,
        student_name=student_name,
        department=department,
        chart_path=chart_path
    )
