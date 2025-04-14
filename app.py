from flask import Flask, render_template, request, jsonify
import mysql.connector
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# === Gemini API Setup ===
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# === MySQL Configuration ===
db_config = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

# === Gemini-based AI Analysis Function ===
def generate_analysis(student_data):
    try:
        prompt = f"""
        Analyze the following student performance data:
        {student_data}
        Provide a detailed performance analysis and helpful academic insights in a friendly, easy-to-understand way.
        """

        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
        response = model.generate_content(
            contents=[{"role": "user", "parts": [prompt]}]
        )
        return response.text
    except Exception as e:
        print("Gemini error:", e)
        return "Sorry, I couldn't generate an analysis at the moment."

# === Get Latest Student Data from MySQL ===
def get_latest_student_data():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row

# === Routes ===
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = """
        INSERT INTO predictions (
            avg_study_hours_per_day, attendance_percent, past_exam_score_1,
            past_exam_score_2, past_exam_score_3, sleep_hours_per_day, internet_usage_hours,
            participation_score, assignments_completed_ratio, extra_curricular_score, predicted_grade
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = tuple(data.values())
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# @app.route('/analysis', methods=['GET'])
# def analysis():
#     latest_data = get_latest_student_data()
#     ai_response = generate_analysis(latest_data)
#     return jsonify({"ai_response": ai_response, "data": latest_data})

@app.route('/analysis', methods=['GET'])
def analysis():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Fetch the latest student's data
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 1")
    student_data = cursor.fetchone()

    # Fetch the average of the relevant fields
    cursor.execute("""
        SELECT 
            AVG(avg_study_hours_per_day) AS avg_study_hours_per_day,
            AVG(attendance_percent) AS attendance_percent,
            AVG(sleep_hours_per_day) AS sleep_hours_per_day,
            AVG(internet_usage_hours) AS internet_usage_hours,
            AVG(participation_score) AS participation_score,
            AVG(assignments_completed_ratio) AS assignments_completed_ratio,
            AVG(extra_curricular_score) AS extra_curricular_score
        FROM predictions
    """)
    average_data = cursor.fetchone()

    conn.close()

    # Generate AI response for this student
    ai_response = generate_analysis(student_data)

    return jsonify({
        "ai_response": ai_response,
        "student_data": student_data,
        "average_data": average_data
    })


if __name__ == '__main__':
    app.run(debug=True)
