from flask import Flask,render_template,request
import joblib

app=Flask(__name__)

model=joblib.load("model/spam_model.pkl")
vectorizer=joblib.load("model/vectorizer.pkl")

@app.route('/')
def home():
    return render_template("index.html")

# Prediction Route
@app.route('/predict', methods=['POST'])
def predict():

    # Get the message entered by the user
    message = request.form['message']

    # Convert the message into TF-IDF features
    message_vector = vectorizer.transform([message])

    # Predict using the trained model
    prediction = model.predict(message_vector)

    # Convert prediction to readable text
    if prediction[0] == 1:
        result = "Spam"
    else:
        result = "Not Spam"

    # Display result on webpage
    return render_template("index.html", prediction=result)

if __name__ == "__main__":
    app.run(debug=True)