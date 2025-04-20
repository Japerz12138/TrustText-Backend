from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from db import init_db

app = Flask(__name__)
CORS(app)

# Serve the HTML form
@app.route("/")
def home():
    return render_template("index.html")

# API endpoint to submit a message
@app.route("/submit", methods=["POST"])
def check_message_api():
    data = request.get_json()
    sms_input = data.get("sms", "").strip().lower()

    if not sms_input:
        return jsonify({"result": "Message cannot be empty."}), 400

    conn = sqlite3.connect("trusttext.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class FROM messages WHERE LOWER(sms) = ?", (sms_input,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"result": f"This message is classified as: {row[0].upper()}"}), 200
    else:
        return jsonify({"result": "Message not found in database. Cannot classify."}), 200


def submit_message():
    data = request.get_json()
    message_class = data.get("class", "").strip().lower()
    sms = data.get("sms", "").strip()

    if message_class not in ["spam", "ham"]:
        return jsonify({"status": "error", "message": "Class must be 'spam' or 'ham'."}), 400
    if not sms:
        return jsonify({"status": "error", "message": "SMS cannot be empty."}), 400

    conn = sqlite3.connect("trusttext.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (class, sms) VALUES (?, ?)", (message_class, sms))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Message stored successfully."})

@app.route("/messages_by_class", methods=["GET"])
def get_messages_by_class():
    msg_class = request.args.get("class", "").strip().lower()

    if msg_class not in ["spam", "ham"]:
        return jsonify({"status": "error", "message": "Invalid class type."}), 400

    conn = sqlite3.connect("trusttext.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE class = ?", (msg_class,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)



# Optional: API to view all messages
@app.route("/messages", methods=["GET"])
def get_messages():
    conn = sqlite3.connect("trusttext.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    rows = cursor.fetchall()
    conn.close()
    return render_template("messages.html", messages=rows)



@app.route("/check_message", methods=["POST"])
def check_message_spam():
    data = request.get_json()
    sms_input = data.get("sms", "").strip().lower()

    if not sms_input:
        return jsonify({"result": "Message cannot be empty."}), 400

    conn = sqlite3.connect("trusttext.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class FROM messages WHERE LOWER(sms) = ?", (sms_input,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"result": f"This message is classified as: {row[0].upper()}"}), 200
    else:
        return jsonify({"result": "Message not found in database. Cannot classify."}), 200
















if __name__ == "__main__":
    init_db()
    app.run(debug=True)
