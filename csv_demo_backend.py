from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import csv
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import shutil

# Initialize Flask app
app = Flask(__name__)
db_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(db_dir, exist_ok=True)

# 🌐 Replace with your actual machine IP address
ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://192.168.50.96:8081",           # 👈 Replace this with your IP
    "exp://192.168.50.96:8081",            # 👈 Replace this too (for Expo Go)
    "*"                                    # Use only for development
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "messages.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    result = db.Column(db.String(10))  # safe / suspicious / dangerous
    matched_pattern = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "result": self.result,
            "matched_pattern": self.matched_pattern,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Global variables
dangerous_patterns = []
suspicious_patterns = []

def load_patterns():
    """Loads patterns from spam.csv or uses defaults if the file doesn't exist."""
    global dangerous_patterns, suspicious_patterns

    # Fallback default patterns
    default_dangerous = ["you've won", "claim your prize", "free money", "lottery winner", "bank details"]
    default_suspicious = ["urgent attention", "gift card", "limited time offer"]

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spam.csv')

    # Auto-copy from backup if spam.csv is missing
    backup_csv_path = '/Users/amnakhwaja/TrustText-Backend/backend/spam.csv'
    if not os.path.exists(csv_path):
        if os.path.exists(backup_csv_path):
            print("📁 spam.csv not found. Copying from backup.")
            shutil.copyfile(backup_csv_path, csv_path)
        else:
            print("⚠️ spam.csv and backup both not found. Using default patterns.")
            dangerous_patterns = default_dangerous
            suspicious_patterns = default_suspicious
            return TfidfVectorizer(), np.array([]), np.array([])

    # Read spam.csv
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # skip header
        dangerous_patterns.clear()
        suspicious_patterns.clear()
        
        for row in reader:
            if len(row) > 1:
                pattern, severity = row[0].strip(), row[1].strip().lower()
                if severity == 'dangerous':
                    dangerous_patterns.append(pattern)
                elif severity == 'suspicious':
                    suspicious_patterns.append(pattern)

    # Fallback again if CSV was empty
    if not dangerous_patterns:
        dangerous_patterns = default_dangerous
    if not suspicious_patterns:
        suspicious_patterns = default_suspicious

    vectorizer = TfidfVectorizer()
    dangerous_vectors = vectorizer.fit_transform(dangerous_patterns)
    suspicious_vectors = vectorizer.transform(suspicious_patterns)

    return vectorizer, dangerous_vectors, suspicious_vectors

def check_text_safety(text, vectorizer, dangerous_vectors, suspicious_vectors):
    """Check similarity of input text with known patterns using cosine similarity."""
    text_vector = vectorizer.transform([text])
    dangerous_sim = cosine_similarity(text_vector, dangerous_vectors).flatten()
    suspicious_sim = cosine_similarity(text_vector, suspicious_vectors).flatten()

    max_dangerous_sim = np.max(dangerous_sim) if dangerous_sim.size > 0 else 0
    max_suspicious_sim = np.max(suspicious_sim) if suspicious_sim.size > 0 else 0

    DANGER_THRESHOLD = 0.3
    SUSPICIOUS_THRESHOLD = 0.15

    if max_dangerous_sim >= DANGER_THRESHOLD:
        return "dangerous", dangerous_patterns[np.argmax(dangerous_sim)]
    elif max_suspicious_sim >= SUSPICIOUS_THRESHOLD:
        return "suspicious", suspicious_patterns[np.argmax(suspicious_sim)]
    else:
        return "safe", None

@app.route('/')
def health_check():
    return "✅ Backend is running!"

@app.route('/check_text', methods=['POST'])
def check_text():
    data = request.json
    text = data.get("text")

    if not text:
        return jsonify({"status": "error", "message": "Text is required"}), 400

    global vectorizer, dangerous_vectors, suspicious_vectors
    if not vectorizer:
        vectorizer, dangerous_vectors, suspicious_vectors = load_patterns()

    result, matched_pattern = check_text_safety(text, vectorizer, dangerous_vectors, suspicious_vectors)

    try:
        new_message = Message(content=text, result=result, matched_pattern=matched_pattern)
        db.session.add(new_message)
        db.session.commit()
    except Exception as e:
        print(f"⚠️ DB Error: {e}")
        db.session.rollback()

    return jsonify({
        "status": "success",
        "result": result,
        "matched_pattern": matched_pattern
    })

@app.route('/messages', methods=['GET'])
def get_messages():
    """Get all previously checked messages."""
    try:
        messages = Message.query.all()
        return jsonify({
            "status": "success",
            "messages": [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reload_patterns', methods=['GET'])
def reload_patterns():
    """Reload patterns from CSV without restarting the server."""
    global vectorizer, dangerous_vectors, suspicious_vectors
    vectorizer, dangerous_vectors, suspicious_vectors = load_patterns()
    return jsonify({"status": "success", "message": "Patterns reloaded!"})

# Initialize app and run
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    vectorizer, dangerous_vectors, suspicious_vectors = load_patterns()
    app.run(debug=True, host="0.0.0.0", port=5000)
