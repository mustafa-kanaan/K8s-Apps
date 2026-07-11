from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

# DB config comes from environment variables — injected by ConfigMap/Secret
db_config = {
    "host": os.environ.get("DB_HOST", "mysql"),      # Service name, not IP
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD"),        # From Secret
    "database": os.environ.get("DB_NAME", "tododb")
}

def get_connection():
    return mysql.connector.connect(**db_config)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task VARCHAR(255) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS request_counter (
            id INT PRIMARY KEY,
            count INT NOT NULL
        )
    """)
    cur.execute("INSERT IGNORE INTO request_counter (id, count) VALUES (1, 0)")
    conn.commit()
    cur.close()
    conn.close()

def increment_counter():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE request_counter SET count = count + 1 WHERE id = 1")
    conn.commit()
    cur.close()
    conn.close()

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/todos", methods=["GET"])
def get_todos():
    increment_counter()
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM todos")
    todos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(todos)

@app.route("/todos", methods=["POST"])
def add_todo():
    increment_counter()
    task = request.json.get("task")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO todos (task) VALUES (%s)", (task,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "todo added"}), 201

@app.route("/stats", methods=["GET"])
def stats():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT count FROM request_counter WHERE id = 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({"total_requests": result["count"]})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)