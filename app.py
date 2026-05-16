from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import random
import requests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------------
# DATABASE INIT
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
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error = "Please fill in all fields."
            return render_template("register.html", error=error)

        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_pw)
            )
            conn.commit()
        except:
            error = "Username already exists."
            return render_template("register.html", error=error)
        finally:
            conn.close()

        return redirect("/login")

    return render_template("register.html", error=error)

# -------------------------
# LOGIN (FIXED)
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error = "Please enter both username and password."
            return render_template("login.html", error=error)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect("/dashboard")

        error = "Invalid username or password."

    return render_template("login.html", error=error)

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
# DASHBOARD (FULL FIXED VERSION)
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    try:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT id, task, day FROM tasks WHERE user_id = ?",
            (session["user_id"],)
        )
        tasks = c.fetchall()
        conn.close()

        # -------------------------
        # TASK DATA FOR CHART
        # -------------------------
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
            if len(t) >= 3 and t[2] in task_data:
                task_data[t[2]] += 1

        # -------------------------
        # QUOTE — random quote on each request
        # -------------------------
        fallback_quotes = [
            "Stay consistent — success is built daily.",
            "The secret of getting ahead is getting started. — Mark Twain",
            "It always seems impossible until it's done. — Nelson Mandela",
            "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
            "Start where you are. Use what you have. Do what you can. — Arthur Ashe",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. — Winston Churchill",
            "Believe you can and you're halfway there. — Theodore Roosevelt",
            "The only way to do great work is to love what you do. — Steve Jobs",
            "Hard work beats talent when talent doesn't work hard. — Tim Notke",
            "You don't have to be great to start, but you have to start to be great. — Zig Ziglar",
            "Dream big and dare to fail. — Norman Vaughan",
            "What you do today can improve all your tomorrows. — Ralph Marston",
            "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
            "Education is the most powerful weapon which you can use to change the world. — Nelson Mandela",
            "A person who never made a mistake never tried anything new. — Albert Einstein",
            "In the middle of every difficulty lies opportunity. — Albert Einstein",
            "It does not matter how slowly you go as long as you do not stop. — Confucius",
            "Act as if what you do makes a difference. It does. — William James",
            "Quality is not an act, it is a habit. — Aristotle",
            "Well done is better than well said. — Benjamin Franklin",
        ]

        quote = random.choice(fallback_quotes)

        try:
            response = requests.get(
                "https://zenquotes.io/api/quotes",
                timeout=3
            )

            if response.ok:
                data = response.json()
                pick = random.choice(data)
                quote_text = pick.get("q")
                quote_author = pick.get("a")

                if quote_text and quote_author and "Too many requests" not in quote_text:
                    quote = f"{quote_text} — {quote_author}"

        except Exception as e:
            print("Quote API error:", e)

        # -------------------------
        # TIP
        # -------------------------
        tip = "Break big tasks into small steps and stay consistent."

        # -------------------------
        # RENDER
        # -------------------------
        return render_template(
            "dashboard.html",
            username=session.get("username"),
            tasks=tasks,
            task_data=task_data,
            quote=quote,
            tip=tip
        )

    except Exception as e:
        print("Dashboard error:", e)
        return "Dashboard error — check server logs"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
