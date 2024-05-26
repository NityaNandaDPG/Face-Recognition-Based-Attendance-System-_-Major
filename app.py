from flask import Flask, render_template, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Route to the index page
@app.route('/')
def index():
    return render_template('index.html', selected_date='', no_data=False)

# Route to handle attendance data for a specific date
@app.route('/attendance', methods=['POST'])
def attendance():
    selected_date = request.form.get('selected_date')
    course = request.form.get('course')
    semester = request.form.get('semester')
    subject = request.form.get('subject')
    
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    formatted_date = selected_date_obj.strftime('%Y-%m-%d')

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # cursor.execute("SELECT name, entrytime, exittime FROM attendance WHERE date = ?", (formatted_date,))
    cursor.execute("""
        SELECT name, entrytime, exittime 
        FROM attendance 
        WHERE date = ? AND course = ? AND semester = ? AND subject = ?
    """, (formatted_date, course, semester, subject))
    attendance_data = cursor.fetchall()

    # Calculate attendance eligibility and add it to the tuple
    updated_attendance_data = []
    for name, entry_time, exit_time in attendance_data:
        entry_time_obj = datetime.strptime(entry_time, '%H:%M:%S')
        exit_time_obj = datetime.strptime(exit_time, '%H:%M:%S')
        duration = exit_time_obj - entry_time_obj
        attendance_eligible = duration >= timedelta(hours=1)
        updated_attendance_data.append((name, entry_time, exit_time, attendance_eligible))

    conn.close()

    if not attendance_data:
        return render_template('index.html', selected_date=selected_date, no_data=True)
    
    return render_template('index.html', selected_date=selected_date, attendance_data=updated_attendance_data)

# Function to calculate and retrieve average attendance
def get_average_attendance(course, semester, subject):   
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    query = """
    SELECT name, 
           COUNT(*) as total_days,
           ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM attendance WHERE course = ? AND semester = ? AND subject = ?), 2) as average_attendance
    FROM attendance
    WHERE course = ? AND semester = ? AND subject = ?
    GROUP BY name;
    """
    cursor.execute(query, (course, semester, subject, course, semester, subject))
    data = cursor.fetchall()
    conn.close()
    return data

# Route to handle the request for average attendance


@app.route('/overall_attendance', methods=['GET', 'POST'])
def average_attendance():
    if request.method == 'POST':
        course = request.form.get('course')
        semester = request.form.get('semester')
        subject = request.form.get('subject')

        avg_attendance_data = get_average_attendance(course, semester, subject)
        return render_template('overall_attendance.html', avg_attendance_data=avg_attendance_data)
    
    # For GET request, render the form
    return render_template('overall_attendance.html')


if __name__ == '__main__':
    app.run(debug=True)