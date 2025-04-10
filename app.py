from flask import Flask, render_template
from flask import send_file
import pandas as pd
import plotly.express as px
import os
from flask import request
from flask import session

app = Flask(__name__)

app.secret_key = 'secret123'

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST':
        user_msg = request.form['message']
        bot_reply = f"Bot says: You said '{user_msg}'"
        session['chat_history'].append(("You", user_msg))
        session['chat_history'].append(("Bot", bot_reply))
        session.modified = True
    return render_template("chat.html", history=session['chat_history'])

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/health')
def health():
    data = pd.read_csv("static/data/health_monitoring.csv").tail(100)
    fig = px.line(data, x='Timestamp', y='Heart Rate', title='Heart Rate Over Time')
    chart = fig.to_html(full_html=False)
    return render_template("health.html", data=data[['Timestamp', 'Heart Rate', 'Blood Pressure']].to_dict(orient='records'), chart=chart)

@app.route("/reminders")
def reminders():
    df = pd.read_csv("static/data/daily_reminder.csv").tail(100)

    # Rename columns to fix extra spaces and unify naming
    df.columns = [col.strip() for col in df.columns]

    # Create a new DataFrame with cleaned columns
    df_clean = pd.DataFrame({
        'Time': df['Scheduled Time'],
        'Reminder': df['Reminder Type'],
        'Type': df['Reminder Type'],
        'Status': df.apply(lambda row: 'Done' if str(row['Acknowledged (Yes/No)']).strip().lower() == 'yes' else 'Pending', axis=1)
    })

    # Pass to HTML template
    return render_template("reminders.html", data=df_clean.to_dict(orient='records'))


@app.route('/fall')
def fall():
    data = pd.read_csv("static/data/safety_monitoring.csv").tail(100)
    data.rename(columns={"Timestamp": "Time"}, inplace=True)
    data['Status'] = data['Fall Detected (Yes/No)']
    fig = px.bar(data, x='Location', title='Falls by Location')
    chart = fig.to_html(full_html=False)
    return render_template("fall.html", data=data[['Time', 'Location', 'Status']].to_dict(orient='records'), chart=chart)

@app.route('/emergency')
def emergency():
    try:
        data = pd.read_csv("static/data/safety_monitoring.csv")
        last_fall = data['Fall Detected (Yes/No)'].iloc[-1].lower()
        emergency_on = last_fall == "yes"
    except:
        emergency_on = False
    return render_template("emergency.html", emergency_on=emergency_on)

@app.route('/chatbot')
def chatbot():
    return render_template("chatbot.html")

@app.route('/diet-day/<int:day>')
def get_diet_day(day):
    import pandas as pd
    from flask import jsonify

    try:
        df = pd.read_csv('static/data/diet_plan.csv')

        if 1 <= day <= len(df):
            row = df[df['Day'] == day]

            if not row.empty:
                meals = {
                    'Breakfast': row.iloc[0]['Breakfast'],
                    'Lunch': row.iloc[0]['Lunch'],
                    'Dinner': row.iloc[0]['Dinner'],
                    'Snacks': row.iloc[0]['Snacks']
                }

                html_content = f"""
                    <ul>
                        <li><strong>Breakfast:</strong> {meals['Breakfast']}</li>
                        <li><strong>Lunch:</strong> {meals['Lunch']}</li>
                        <li><strong>Dinner:</strong> {meals['Dinner']}</li>
                        <li><strong>Snacks:</strong> {meals['Snacks']}</li>
                    </ul>
                """
                return jsonify({'html': html_content})
            else:
                return jsonify({'html': 'No data found for this day.'})
        else:
            return jsonify({'html': 'Invalid day selected.'})
    except Exception as e:
        return jsonify({'html': f'Error loading diet data: {e}'})


@app.route("/diet")
def diet():
    df = pd.read_csv("static/data/diet_plan.csv")
    df.columns = [col.strip() for col in df.columns]  # Clean any extra spaces
    data = df.to_dict(orient='records')
    return render_template("diet.html", data=data)


@app.route('/medications')
def medications():
    return render_template("medications.html")

@app.route('/caregiver')
def caregiver():
    # Load health data
    health_df = pd.read_csv('static/data/health_monitoring.csv').tail(50)
    heart_rates = health_df['Heart Rate'].tolist()
    timestamps = health_df['Timestamp'].tolist()

    # Load reminder data and process it
    reminder_df = pd.read_csv('static/data/daily_reminder.csv')
    reminder_df.columns = [col.strip() for col in reminder_df.columns]

    reminders = []
    for _, row in reminder_df.iterrows():
        reminders.append({
            "task": row.get("Reminder Type", "N/A"),
            "time": row.get("Scheduled Time", "N/A"),
            "status": "done" if str(row.get("Acknowledged (Yes/No)", "")).strip().lower() == "yes" else "pending"
        })

    # Load fall data and format
    fall_df = pd.read_csv('static/data/safety_monitoring.csv')
    fall_data = []
    for _, row in fall_df.iterrows():
        fall_data.append({
            "timestamp": row.get("Timestamp", "N/A"),
            "fall_detected": str(row.get("Fall Detected (Yes/No)", "no")).strip().lower() == "yes"
        })

    # Dummy AI risk prediction values (replace with real model later if needed)
    risk_values = [12, 5, 3]  # low, medium, high

    return render_template("caregiver.html",
                           heart_rates=heart_rates,
                           timestamps=timestamps,
                           reminders=reminders,
                           fall_data=fall_data,
                           risk_values=risk_values)


@app.route('/download_health_data')
def download_health_data():
    return send_file('static/data/health_monitoring.csv', as_attachment=True)

@app.route('/save-note', methods=['POST'])
def save_note():
    data = request.get_json()
    note = data.get('note', '')
    with open('caregiver_notes.txt', 'a', encoding='utf-8') as f:
        f.write(note + '\n')
    return "Note saved successfully!"

if __name__ == '__main__':
    app.run(debug=True)