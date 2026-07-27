from flask import Flask,render_template,request,redirect, url_for
import joblib
import sqlite3
import bcrypt

app=Flask(__name__)

model=joblib.load("model/spam_model.pkl")
vectorizer=joblib.load("model/vectorizer.pkl")

# Function to identify spam category
def detect_category(message):

    message = message.lower()

    # Banking Scam
    if any(word in message for word in [
        "bank", "account", "otp",
        "debit", "credit",
        "sbi", "hdfc", "icici",
        "kyc"
    ]):
        return "🏦 Banking Scam"

    # Lottery Scam
    elif any(word in message for word in [
        "lottery",
        "winner",
        "won",
        "prize",
        "jackpot",
        "lucky draw",
        "congratulations",
        "claim"
    ]):
        return "🎁 Lottery Scam"

    # Fake Invoice
    elif any(word in message for word in [
        "invoice",
        "bill",
        "payment",
        "receipt",
        "due"
    ]):
        return "📄 Fake Invoice"

    # Crypto Scam
    elif any(word in message for word in [
        "bitcoin",
        "crypto",
        "investment",
        "profit",
        "trading"
    ]):
        return "💰 Crypto Scam"

    # Phishing
    elif any(word in message for word in [
        "login",
        "password",
        "verify account",
        "update account",
        "click here",
        "link"
    ]):
        return "🎣 Phishing"

    else:
        return "⚠ General Spam"

@app.route("/")
def login():
    return render_template("login.html")

from flask import request

@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]

    # Connect to database
    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    conn.close()

    # Check if email exists
    if user is None:
        return "User not found!"

    # Verify password
    stored_password = user[3]

    if bcrypt.checkpw(password.encode("utf-8"),
                      stored_password.encode("utf-8")):

        return redirect(url_for("dashboard"))
    

    else:
        return "Incorrect Password!"

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match!"

        # Hash the password
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        # Connect to database
        conn = sqlite3.connect("spam.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users(fullname, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    fullname,
                    email,
                    hashed_password.decode("utf-8")
                )
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already exists!"

        conn.close()

        return "Registration Successful!"

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scan_history")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scan_history WHERE prediction='Spam'")
    spam = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scan_history WHERE prediction='Not Spam'")
    safe = cursor.fetchone()[0]

    categories = [
        "🏦 Banking Scam",
        "🎁 Lottery Scam",
        "🎣 Phishing",
        "📄 Fake Invoice",
        "💰 Crypto Scam"
    ]

    counts = []

    for category in categories:
        cursor.execute(
            "SELECT COUNT(*) FROM scan_history WHERE category=?",
            (category,)
        )
        counts.append(cursor.fetchone()[0])

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        spam=spam,
        safe=safe,
        category_counts=counts
    )

@app.route("/detect")
def detect():
    return render_template("detect.html")

# Prediction Route

@app.route('/predict', methods=['POST'])
def predict():

    message = request.form['message']
    print(f"Message received: '{message}'")
    message = message.strip()

    if message == "":
        return render_template(
            "detect.html",
            prediction="Please enter a message.",
            category=""
        )

    # Check category first
    category = detect_category(message)

    # If it matches a known scam category,
    # directly classify it as Spam
    if category != "⚠ General Spam":
        result = "Spam"

    else:
        # Otherwise use the ML model
        message_vector = vectorizer.transform([message])
        prediction = model.predict(message_vector)

        if prediction[0] == 1:
            result = "Spam"
            category = "⚠ General Spam"
        else:
            result = "Not Spam"
            category = ""

    # Save scan history
    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scan_history
        (email, message, prediction, category)
        VALUES (?, ?, ?, ?)
        """,
    (
        "Current User",   # We'll replace this with the logged-in user's email later
        message,
        result,
        category
    ))

    conn.commit()
    conn.close()

    return render_template(
        "detect.html",
        prediction=result,
        category=category
    )

@app.route("/history")
def history():

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scan_history")

    rows = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=rows
    )

if __name__ == "__main__":
    app.run(debug=True)