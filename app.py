from flask import Flask, render_template, request, redirect, session
import random
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"


# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ================= MEMORY STORAGE =================
mood_history = []

quotes = [
    "You don’t have to be perfect, just consistent 💛",
    "Small steps still move you forward 🌱",
    "Rest is productive too 😌",
    "You are stronger than you think 💪",
    "Every day is a fresh start ✨"
]


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (user, pw)
        )
        result = cur.fetchone()
        conn.close()

        if result:
            session["user"] = user
            return redirect("/")
        else:
            return render_template("login_error.html")

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (?,?)", (user, pw))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ================= HOME =================
@app.route("/")
def index():
    # If logged in → show home
    if "user" in session:
        if "theme" not in session:
            session["theme"] = "light"
        return render_template("home.html")

    # Otherwise → login page first
    return redirect("/login")


# ================= PROFILE =================
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        return render_template("assessment.html")

    return render_template("profile.html")


# ================= ASSESSMENT =================
@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        sleep = int(request.form.get("sleep", 0))
        mood = int(request.form.get("mood", 0))
        pressure = int(request.form.get("pressure", 0))

        score = sleep + mood + pressure

        if score <= 3:
            level = "Low Stress"
            advice = "Great job! Maintain your routine 🌿"
            emoji = "😄"
        elif score <= 6:
            level = "Moderate Stress"
            advice = "Take breaks and talk to friends 💛"
            emoji = "😐"
        else:
            level = "High Stress"
            advice = "Please slow down and seek support 🤝"
            emoji = "😣"

        quote = random.choice(quotes)

        return render_template(
            "result.html",
            score=score,
            level=level,
            advice=advice,
            emoji=emoji,
            quote=quote
        )

    return render_template("assessment.html")


# ================= MOOD TRACKER =================
@app.route("/mood", methods=["GET", "POST"])
def mood():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        mood = request.form.get("mood")
        journal = request.form.get("journal")

        mood_history.append(mood)

    return render_template("mood.html", history=mood_history)


# ================= SUPPORT =================
@app.route("/support")
def support():
    if "user" not in session:
        return redirect("/login")

    return render_template("support.html")


# ================= SETTINGS =================
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        session["theme"] = request.form.get("theme")
        session["lang"] = request.form.get("lang")

    return render_template("settings.html")


# ================= HELP PAGE =================
@app.route("/help")
def help_page():
    if "user" not in session:
        return redirect("/login")

    return render_template("help.html")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)