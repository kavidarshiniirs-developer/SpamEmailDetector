from flask import Flask,render_template,request,redirect, url_for,flash,session
import joblib
import sqlite3
import bcrypt
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

app=Flask(__name__)
app.secret_key = "spam_detector_secret_key"

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
        flash("Email does not exist!", "error")
        return redirect(url_for("login"))

    # Verify password
    stored_password = user[3]

    if bcrypt.checkpw(password.encode("utf-8"),
                      stored_password.encode("utf-8")):

        session["user_email"] = email
        flash("Login Successful!", "success")
        
        return redirect(url_for("dashboard"))
    

    else:
        flash("Incorrect Password!", "error")
        return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check if passwords match
        if password != confirm_password:
            flash("❌ Passwords do not match!","error")
            return redirect(url_for("register"))

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
            flash("❌ Email already exists!","error")
            return redirect(url_for("register"))

        conn.close()

        flash("✅ Registration Successful! Please login.","success")
        return redirect(url_for("login"))

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

    message_vector = vectorizer.transform([message])
    prediction = model.predict(message_vector)

# Prediction probability
    probability = model.predict_proba(message_vector)

    confidence = round(max(probability[0]) * 100, 2)

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

# Get prediction probabilities
        probability = model.predict_proba(message_vector)

# Calculate confidence percentage
        confidence = round(max(probability[0]) * 100, 2)

        if prediction[0] == 1:
            result = "Spam"

            if category == "⚠ General Spam":
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
    category=category,
    confidence=confidence
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

@app.route("/delete_history/<int:id>")
def delete_history(id):

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM scan_history WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("🗑 Record deleted successfully!", "success")

    return redirect(url_for("history"))

@app.route("/clear_history")
def clear_history():

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM scan_history")

    conn.commit()
    conn.close()

    flash("All history cleared!", "success")

    return redirect(url_for("history"))

@app.route("/clustering")
def clustering():

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT message
        FROM scan_history
        WHERE prediction='Spam'
    """)

    rows = cursor.fetchall()

    conn.close()

    messages = [row[0] for row in rows]

    if len(messages) < 2:
        return render_template(
            "clustering.html",
            clusters=[],
            cluster_counts=[0,0,0]
        )

    # TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(messages)

    # K-Means
    kmeans = KMeans(
        n_clusters=3,
        random_state=42,
        n_init=10
    )

    labels = kmeans.fit_predict(X)

    # Reduce dimensions for scatter plot
    pca = PCA(n_components=2)
    points = pca.fit_transform(X.toarray())

    results = []

    cluster_counts = [0,0,0]

    for i in range(len(messages)):

        cluster_counts[labels[i]] += 1

        results.append({

            "message": messages[i],

            "cluster": int(labels[i]),

            "x": float(points[i][0]),

            "y": float(points[i][1])

        })

    return render_template(

        "clustering.html",

        clusters=results,

        cluster_counts=cluster_counts

    )

@app.route("/profile")
def profile():

    if "user_email" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fullname, email
        FROM users
        WHERE email=?
    """, (session["user_email"],))

    user = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM scan_history")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM scan_history
        WHERE prediction='Spam'
    """)
    spam = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        fullname=user[0],
        email=user[1],
        total=total,
        spam=spam
    )

@app.route("/update_profile", methods=["POST"])
def update_profile():

    if "user_email" not in session:
        return redirect(url_for("login"))

    fullname = request.form["fullname"]
    email = request.form["email"]

    conn = sqlite3.connect("spam.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET fullname=?, email=?
        WHERE email=?
    """, (
        fullname,
        email,
        session["user_email"]
    ))

    conn.commit()
    conn.close()

    # Update the session if the email changed
    session["user_email"] = email

    flash("Profile updated successfully!", "success")

    return redirect(url_for("profile"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("New passwords do not match!", "error")
            return redirect(url_for("change_password"))

        conn = sqlite3.connect("spam.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE email=?",
            (session["user_email"],)
        )

        user = cursor.fetchone()

        if user is None:
            conn.close()
            flash("User not found!", "error")
            return redirect(url_for("change_password"))

        stored_password = user[0]

        if not bcrypt.checkpw(
            current_password.encode("utf-8"),
            stored_password.encode("utf-8")
        ):
            conn.close()
            flash("Current password is incorrect!", "error")
            return redirect(url_for("change_password"))

        hashed_password = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            UPDATE users
            SET password=?
            WHERE email=?
            """,
            (
                hashed_password,
                session["user_email"]
            )
        )

        conn.commit()
        conn.close()

        flash("Password changed successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("change_password.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)