from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------------
# INIT DB
# -------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT,
            day TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# HOME (WELCOME PAGE)
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Missing fields"

        hashed = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed)
            )
            conn.commit()
        except:
            return "User already exists"
        finally:
            conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------
# ADD TASK
# -------------------------
@app.route("/add", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect("/login")

    task = request.form.get("task")
    day = request.form.get("day")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO tasks (user_id, task, day) VALUES (?, ?, ?)",
        (session["user_id"], task, day)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------------------------
# DELETE TASK
# -------------------------
@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id, task, day FROM tasks WHERE user_id = ?", (session["user_id"],))
    tasks = c.fetchall()
    conn.close()

    task_data = {
        "Sunday": 0,
        "Monday": 0,
        "Tuesday": 0,
        "Wednesday": 0,
        "Thursday": 0,
        "Friday": 0,
        "Saturday": 0
    }

    for t in tasks:
        if t[2] in task_data:
            task_data[t[2]] += 1

    return render_template(
        "dashboard.html",
        username=session.get("username"),
        tasks=tasks,
        task_data=task_data,
        quote="Keep going. You're doing better than you think.",
        tip="Break tasks into small steps."
    )

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)