<<<<<<< HEAD
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session
import random
import sqlite3

app = Flask(__name__)
app.secret_key = "thryve_secret_key_2026"

@app.route("/toggle_theme")
def toggle_theme():
    current = session.get("theme", "light")
    session["theme"] = "dark" if current == "light" else "light"
    return redirect(request.referrer or "/")

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    # moods table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS moods(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        mood TEXT,
        journal TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# call the function AFTER defining it
init_db()


# ================= MEMORY STORAGE =================
mood_history = []

quotes = {
    "en": [
        "You don’t have to be perfect, just consistent 💛",
        "Small steps still move you forward 🌱",
        "Rest is productive too 😌",
        "You are stronger than you think 💪",
        "Every day is a fresh start ✨"
    ],
    "bn": [
        "আপনাকে নিখুঁত হতে হবে না, ধারাবাহিক থাকাই যথেষ্ট 💛",
        "ছোট পদক্ষেপও আপনাকে এগিয়ে নিয়ে যায় 🌱",
        "বিশ্রামও ফলপ্রসূ 😌",
        "আপনি যতটা ভাবেন তার চেয়েও শক্তিশালী 💪",
        "প্রতিটি দিন একটি নতুন শুরু ✨"
    ],
    "hi": [
        "आपको परफेक्ट नहीं, निरंतर रहना है 💛",
        "छोटे कदम भी आगे बढ़ाते हैं 🌱",
        "आराम भी उपयोगी है 😌",
        "आप जितना सोचते हैं उससे अधिक मजबूत हैं 💪",
        "हर दिन एक नई शुरुआत है ✨"
    ]
}

# ================= MOOD SCORE MAP =================

mood_score = {
    "good": 4,
    "ok": 3,
    "low": 2,
    "stress": 1
}


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = request.form["username"]
        pw = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=?", (user,))
        result = cur.fetchone()

        conn.close()

        if result and check_password_hash(result[1], pw):

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

        # HASH THE PASSWORD
        pw = generate_password_hash(request.form["password"])

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


@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if "user" not in session:
        return redirect("/login")

    # ✅ MOVE THIS HERE
    lang = session.get("lang", "en")
    t = TEXT.get(lang, TEXT["en"])

    if request.method == "POST":

        sleep = int(request.form.get("sleep", 0))
        mood = int(request.form.get("mood", 0))
        pressure = int(request.form.get("pressure", 0))

        score = sleep + mood + pressure

        if score <= 3:
            level = t["low_stress"]
            advice = t["advice_low"]
            emoji = "😄"
        elif score <= 6:
            level = t["moderate_stress"]
            advice = t["advice_mid"]
            emoji = "😐"
        else:
            level = t["high_stress"]
            advice = t["advice_high"]
            emoji = "😣"

        quote = random.choice(quotes.get(lang, quotes["en"]))

        return render_template(
            "result.html",
            score=score,
            level=level,
            advice=advice,
            emoji=emoji,
            quote=quote,
            t=t   # ✅ ALSO PASS t HERE
        )

    return render_template("assessment.html", t=t)

# ================= MOOD TRACKER =================
@app.route("/mood", methods=["GET", "POST"])
def mood():

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if request.method == "POST":

        mood = request.form.get("mood")
        journal = request.form.get("journal")

        cur.execute(
            "INSERT INTO moods (username, mood, journal) VALUES (?,?,?)",
            (user, mood, journal)
        )

        conn.commit()

    # Fetch mood history
    cur.execute(
        "SELECT mood, journal, date FROM moods WHERE username=? ORDER BY date DESC",
        (user,)
    )

    history = cur.fetchall()

    conn.close()

    return render_template("mood.html", history=history)

@app.route("/mood_history")
def mood_history():

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    lang = session.get("lang", "en")
    t = TEXT.get(lang, TEXT["en"])

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT mood, journal, date FROM moods WHERE username=? ORDER BY date DESC",
        (user,)
    )

    rows = cur.fetchall()

    conn.close()

    history = []

    emoji_map = {
        "good": "😊",
        "ok": "😐",
        "low": "😞",
        "stress": "😣"
    }

    for mood, journal, date in rows:

        emoji = emoji_map.get(mood, "🙂")

        date_only = date.split(" ")[0]   # removes time

        history.append((emoji, journal, date_only))

    return render_template("mood_history.html", history=history, t=t)

# ================= DAILY MOOD RESULT =================

@app.route("/mood_result")
def mood_result():

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    lang = session.get("lang", "en")
    t = TEXT.get(lang, TEXT["en"])

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT mood FROM moods WHERE username=? AND date(date)=date('now')",
        (user,)
    )

    data = cur.fetchall()
    conn.close()

    if not data:
        result = t["no_data"]

    else:

        scores = []

        for m in data:
            mood = m[0]
            scores.append(mood_score.get(mood, 3))

        avg = sum(scores) / len(scores)

        if avg >= 3.5:
            result = t["day_positive"]

        elif avg >= 2.5:
            result = t["day_balanced"]

        elif avg >= 1.5:
            result = t["day_low"]

        else:
            result = t["day_stress"]

    return render_template("mood_result.html", result=result, t=t)

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
        
        session["lang"] = request.form.get("lang")

    return render_template("settings.html")


# ================= HELP PAGE =================
@app.route("/help")
def help_page():
    if "user" not in session:
        return redirect("/login")

    return render_template("help.html")



# ================= GLOBAL LANGUAGE PACK =================

TEXT = {
    "en": {
        "settings": "Settings",
        "language": "Language",
        "save": "Save Settings",

        "home_sub": "Your safe companion for managing stress, emotions, and academic pressure 💛",
        "start": "Start Assessment",

        "profile_title": "Enter Your Details",
        "profile_sub": "Please fill out the information below to proceed.",
        "name": "Name",
        "age": "Age",
        "name_ph": "Enter your name",
        "age_ph": "Select age group",
        "age_1": "11 – 13 (Early Teens)",
        "age_2": "14 – 16 (High School)",
        "age_3": "17 – 19 (Senior Secondary)",
        "age_4": "20 – 22 (Undergraduate)",
        "age_5": "23 – 25 (Postgraduate)",
        "course": "Course",
        "next": "Next ➤",
        
        "course_ph": "Enter your course",

        "assessment_title": "Stress Assessment",
        "assessment_sub": "Answer the questions below to assess your stress level.",
        "sleep": "Sleep Hours",
        "mood": "Mood",
        "pressure": "Family Pressure",
        "check": "Check Stress Level ➤",
        "sleep_low": "Less than 5 hrs",
        "sleep_mid": "5–7 hrs",
        "sleep_high": "More than 7 hrs",

        "low_stress": "Low Stress",
        "moderate_stress": "Moderate Stress",
        "high_stress": "High Stress",

        "advice_low": "Great job! Maintain your routine 🌿",
        "advice_mid": "Take breaks and talk to friends 💛",
        "advice_high": "Please slow down and seek support 🤝",

        "result_title": "Your Stress Result",
        "stress_level": "Stress Level",
        "motivation": "Motivation",
        "relax": "Quick Relax Tools",
        "track_mood": "Track Mood",
        "get_support": "Get Support",

        "mood_low": "Very Low",
        "mood_mid": "Neutral",
        "mood_high": "Good",

        "press_high": "High",
        "press_mid": "Moderate",
        "press_low": "Low",

        "mood_good": "Feeling Good",
        "mood_ok": "Okay",
        "mood_low": "Low",
        "mood_stress": "Very Stressed",

        "mood_title": "Daily Mood Tracker",
        "mood_question": "How are you feeling today?",
        "save_btn": "Save",
        "history": "Mood History",
        "journal_ph": "Write your thoughts...",
        "back_home": "Back Home",

        "support_title": "Support Resources",
        "support_text": "If you feel overwhelmed, you are not alone 💛",

        "helpline": "Helpline",
        "helpline_name": "Kiran Mental Health Helpline",

        "tip_friend": "Talk to a trusted friend",
        "tip_teacher": "Share concerns with a teacher",
        "tip_counselor": "Seek professional counseling",

        "tips": "Self-Care Tips",
        "tip1": "Take slow deep breaths",
        "tip2": "Get enough sleep",
        "tip3": "Stay hydrated",

        "help_title": "How to Use the App",
        "help1": "Click Start Assessment",
        "help2": "Enter your details",
        "help3": "Answer questions",
        "help4": "View results",
        "help5": "Track mood daily",
        "help6": "Use support resources",
        "help_end": "This app helps students manage stress 💛",

        "features": "Features",
        "card1_title": "Track Stress",
        "card1_text": "Understand your stress level",
        "card2_title": "Mood Tracker",
        "card2_text": "Record daily feelings",
        "card3_title": "Relax Tools",
        "card3_text": "Quick calming exercises",
        "card4_title": "Motivation",
        "card4_text": "Stay positive every day",

        "lang_en": "English",
        "lang_hi": "Hindi",
        "lang_bn": "Bengali",

        "day_positive": "You had a very positive day 😊",
"day_balanced": "Your mood was balanced today 🙂",
"day_low": "You seemed a little low today 😔",
"day_stress": "You seemed stressed today 😣",
"no_data": "No mood data for today",
"view_history": "View Mood History",
"history_title": "Mood History",
"nav_home": "Home",
"nav_assessment": "Assessment",
"nav_mood": "Mood",
"nav_support": "Support",
"nav_settings": "Settings",
"nav_help": "Help",
"nav_logout": "Logout"
    },


    "hi": {
    "settings": "सेटिंग्स",
    "language": "भाषा",
    "save": "सेटिंग्स सेव करें",

    "home_sub": "तनाव, भावनाओं और पढ़ाई के दबाव को संभालने में आपका साथी 💛",
    "start": "मूल्यांकन शुरू करें",

    "profile_title": "अपना विवरण दर्ज करें",
    "profile_sub": "आगे बढ़ने के लिए जानकारी भरें।",
    "name": "नाम",
    "age": "आयु",
    "age_ph": "आयु समूह चुनें",
    "age_1": "11 – 13 (किशोरावस्था प्रारंभ)",
    "age_2": "14 – 16 (हाई स्कूल)",
    "age_3": "17 – 19 (सीनियर सेकेंडरी)",
    "age_4": "20 – 22 (स्नातक)",
    "age_5": "23 – 25 (स्नातकोत्तर)",
    "course": "कोर्स",
    "next": "आगे ➤",
    "name_ph": "अपना नाम दर्ज करें",
    
    "course_ph": "अपना कोर्स दर्ज करें",

    "assessment_title": "तनाव मूल्यांकन",
    "assessment_sub": "नीचे दिए प्रश्नों के उत्तर दें।",
    "sleep": "नींद के घंटे",
    "mood": "मूड",
    "pressure": "पारिवारिक दबाव",
    "check": "तनाव स्तर देखें ➤",

    "sleep_low": "5 घंटे से कम",
    "sleep_mid": "5–7 घंटे",
    "sleep_high": "7 घंटे से अधिक",

    "low_stress": "कम तनाव",
    "moderate_stress": "मध्यम तनाव",
    "high_stress": "अधिक तनाव",

    "advice_low": "बहुत अच्छा! अपनी दिनचर्या बनाए रखें 🌿",
    "advice_mid": "ब्रेक लें और दोस्तों से बात करें 💛",
    "advice_high": "कृपया धीमे चलें और सहायता लें 🤝",

    "result_title": "आपका तनाव परिणाम",
    "stress_level": "तनाव स्तर",
    "motivation": "प्रेरणा",
    "relax": "त्वरित आराम उपाय",
    "track_mood": "मूड ट्रैक करें",
    "get_support": "सहायता प्राप्त करें",

    "mood_low": "बहुत खराब",
    "mood_mid": "सामान्य",
    "mood_high": "अच्छा",

    "press_high": "अधिक",
    "press_mid": "मध्यम",
    "press_low": "कम",

    "mood_good": "अच्छा महसूस कर रही हूँ",
    "mood_ok": "ठीक हूँ",
    "mood_stress": "बहुत तनाव में",

    "mood_title": "दैनिक मूड ट्रैकर",
    "mood_question": "आज आप कैसा महसूस कर रही हैं?",
    "save_btn": "सेव करें",
    "history": "मूड इतिहास",
    "journal_ph": "अपने विचार लिखें...",
    "back_home": "होम पर जाएँ",

    "support_title": "सहायता संसाधन",
    "support_text": "यदि आप परेशान हैं, तो आप अकेले नहीं हैं 💛",

    "helpline": "हेल्पलाइन",
    "helpline_name": "किरण मानसिक स्वास्थ्य हेल्पलाइन",

    "tip_friend": "विश्वसनीय मित्र से बात करें",
    "tip_teacher": "शिक्षक से अपनी चिंता साझा करें",
    "tip_counselor": "पेशेवर काउंसलिंग लें",

    "tips": "स्वयं देखभाल सुझाव",
    "tip1": "धीरे-धीरे गहरी सांस लें",
    "tip2": "पर्याप्त नींद लें",
    "tip3": "पानी पिएँ",

    "help_title": "ऐप का उपयोग कैसे करें",
    "help1": "‘मूल्यांकन शुरू करें’ बटन पर क्लिक करें",
    "help2": "अपनी जानकारी दर्ज करें",
    "help3": "प्रश्नों का उत्तर दें",
    "help4": "परिणाम देखें",
    "help5": "रोज़ मूड ट्रैक करें",
    "help6": "जरूरत पड़ने पर सहायता लें",
    "help_end": "💛 यह ऐप छात्रों की मदद करता है।",

    "features": "विशेषताएँ",
    "card1_title": "तनाव ट्रैक करें",
    "card1_text": "अपने तनाव स्तर को समझें",
    "card2_title": "मूड ट्रैकर",
    "card2_text": "रोज़ की भावनाएँ रिकॉर्ड करें",
    "card3_title": "आराम उपकरण",
    "card3_text": "त्वरित शांत करने के अभ्यास",
    "card4_title": "प्रेरणा",
    "card4_text": "हर दिन सकारात्मक रहें",

    "lang_en": "अंग्रेज़ी",
    "lang_hi": "हिंदी",
    "lang_bn": "बंगाली",
    "day_positive": "आज आपका दिन बहुत सकारात्मक रहा 😊",
"day_balanced": "आज आपका मूड संतुलित रहा 🙂",
"day_low": "आज आप थोड़ा उदास लगे 😔",
"day_stress": "आज आप तनाव में दिखे 😣",
"no_data": "आज के लिए कोई मूड डेटा नहीं है",
"view_history": "मूड इतिहास देखें",
"history_title": "मूड इतिहास",
"nav_home": "होम",
"nav_assessment": "मूल्यांकन",
"nav_mood": "मूड",
"nav_support": "सहायता",
"nav_settings": "सेटिंग्स",
"nav_help": "मदद",
"nav_logout": "लॉगआउट"
},

    "bn": {
    "settings": "সেটিংস",
    "language": "ভাষা",
    "save": "সেটিংস সংরক্ষণ করুন",

    "home_sub": "চাপ ও আবেগ সামলাতে আপনার সঙ্গী 💛",
    "start": "মূল্যায়ন শুরু করুন",

    "profile_title": "আপনার তথ্য লিখুন",
    "profile_sub": "এগোতে তথ্য পূরণ করুন।",
    "name": "নাম",
    "age": "বয়স",
    "age_ph": "আপনার বয়স নির্বাচন করুন",
    "age_1": "১১ – ১৩ (প্রাথমিক কিশোর)",
    "age_2": "১৪ – ১৬ (হাই স্কুল)",
    "age_3": "১৭ – ১৯ (উচ্চ মাধ্যমিক)",
    "age_4": "২০ – ২২ (স্নাতক)",
    "age_5": "২৩ – ২৫ (স্নাতকোত্তর)",
    "course": "কোর্স",
    "next": "পরবর্তী ➤",
    "name_ph": "আপনার নাম লিখুন",
    
    "course_ph": "আপনার কোর্স লিখুন",

    "assessment_title": "স্ট্রেস মূল্যায়ন",
    "assessment_sub": "প্রশ্নগুলোর উত্তর দিন।",
    "sleep": "ঘুমের সময়",
    "mood": "মুড",
    "pressure": "পারিবারিক চাপ",
    "check": "স্ট্রেস লেভেল দেখুন ➤",

    "sleep_low": "৫ ঘন্টার কম",
    "sleep_mid": "৫–৭ ঘন্টা",
    "sleep_high": "৭ ঘন্টার বেশি",

    "low_stress": "কম স্ট্রেস",
    "moderate_stress": "মাঝারি স্ট্রেস",
    "high_stress": "উচ্চ স্ট্রেস",

    "advice_low": "দারুণ! আপনার রুটিন বজায় রাখুন 🌿",
    "advice_mid": "বিরতি নিন এবং বন্ধুদের সাথে কথা বলুন 💛",
    "advice_high": "ধীরে চলুন এবং প্রয়োজনে সহায়তা নিন 🤝",

    "result_title": "আপনার স্ট্রেস ফলাফল",
    "stress_level": "স্ট্রেস লেভেল",
    "motivation": "প্রেরণা",
    "relax": "দ্রুত আরাম টুলস",
    "track_mood": "মুড ট্র্যাক করুন",
    "get_support": "সহায়তা নিন",

    "mood_low": "খুব খারাপ",
    "mood_mid": "স্বাভাবিক",
    "mood_high": "ভালো",

    "press_high": "উচ্চ",
    "press_mid": "মাঝারি",
    "press_low": "কম",

    "mood_good": "ভালো লাগছে",
    "mood_ok": "ঠিক আছি",
    "mood_stress": "খুব স্ট্রেসে",

    "mood_title": "দৈনিক মুড ট্র্যাকার",
    "mood_question": "আজ আপনি কেমন অনুভব করছেন?",
    "save_btn": "সংরক্ষণ করুন",
    "history": "মুড ইতিহাস",
    "journal_ph": "আপনার ভাবনা লিখুন...",
    "back_home": "হোমে ফিরে যান",

    "support_title": "সহায়তা সংস্থান",
    "support_text": "আপনি একা নন 💛",

    "helpline": "হেল্পলাইন",
    "helpline_name": "কিরণ মানসিক স্বাস্থ্য হেল্পলাইন",

    "tip_friend": "বিশ্বাসযোগ্য বন্ধুর সাথে কথা বলুন",
    "tip_teacher": "শিক্ষকের সাথে আপনার উদ্বেগ শেয়ার করুন",
    "tip_counselor": "পেশাদার কাউন্সেলিং নিন",

    "tips": "স্ব-যত্ন পরামর্শ",
    "tip1": "ধীরে গভীর শ্বাস নিন",
    "tip2": "পর্যাপ্ত ঘুমান",
    "tip3": "পানি পান করুন",

    "help_title": "অ্যাপ কীভাবে ব্যবহার করবেন",
    "help1": "‘মূল্যায়ন শুরু করুন’ বোতামে ক্লিক করুন",
    "help2": "তথ্য লিখুন",
    "help3": "প্রশ্নের উত্তর দিন",
    "help4": "ফলাফল দেখুন",
    "help5": "প্রতিদিন মুড ট্র্যাক করুন",
    "help6": "প্রয়োজনে সহায়তা নিন",
    "help_end": "💛 এই অ্যাপ শিক্ষার্থীদের সাহায্য করে।",

    "features": "বৈশিষ্ট্যসমূহ",
    "card1_title": "স্ট্রেস ট্র্যাক করুন",
    "card1_text": "আপনার স্ট্রেস লেভেল বুঝুন",
    "card2_title": "মুড ট্র্যাকার",
    "card2_text": "প্রতিদিনের অনুভূতি সংরক্ষণ করুন",
    "card3_title": "রিলাক্স টুলস",
    "card3_text": "দ্রুত শান্ত করার অনুশীলন",
    "card4_title": "প্রেরণা",
    "card4_text": "প্রতিদিন ইতিবাচক থাকুন",

    "lang_en": "ইংরেজি",
    "lang_hi": "হিন্দি",
    "lang_bn": "বাংলা",
    "day_positive": "আজ আপনার দিন খুব ইতিবাচক ছিল 😊",
"day_balanced": "আজ আপনার মুড বেশ স্থির ছিল 🙂",
"day_low": "আজ আপনি একটু মন খারাপ লাগছিল 😔",
"day_stress": "আজ আপনি বেশ চাপের মধ্যে ছিলেন 😣",
"no_data": "আজকের জন্য কোনো মুড ডাটা নেই",
"view_history": "মুড ইতিহাস দেখুন",
"history_title": "মুড ইতিহাস",
"nav_home": "হোম",
"nav_assessment": "মূল্যায়ন",
"nav_mood": "মুড",
"nav_support": "সহায়তা",
"nav_settings": "সেটিংস",
"nav_help": "সাহায্য",
"nav_logout": "লগআউট",
}

}

@app.context_processor
def inject_text():
    lang = session.get("lang", "en")
    return dict(t=TEXT.get(lang, TEXT["en"]))

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

    
=======
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
>>>>>>> aa71851d56f68f84064b222d36c1ce05801d53d4
