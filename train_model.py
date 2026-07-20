import pandas as pd
import string
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report

#Pandas used to read the csv file 
#dataset/spam.csv shows the file loc
#the file is stored using latin-1 encoding

data=pd.read_csv("dataset/spam.csv",encoding="latin-1")

#prints first 5 records from the file
'''print(data.head())'''

#Removing the unwanted columns
data=data[['v1','v2']]

#Instead of leaving v1 and v2 i changed the name of columns
data.columns=['label','message']

'''print("\nCleaned Dataset:")
print(data.head())'''

#Data preprocessing-->Machine learning algorithms cannot understand words
# so we convert--> ham  → 0 and spam → 1
#This process is called LABEL ENCODING
data['label']=data['label'].map({'ham':0,'spam':1})
'''print("\nConverted Data:")
print(data.head())'''

#Machine learning models work better if the text is cleaned first.
#So we convert text to lower case and remove all the punctuations.
def clean_text(text):
    text=text.lower()

    text=text.translate(str.maketrans('','',string.punctuation))
    return text
data['message']=data['message'].apply(clean_text)

'''print("\nCleaned Messages")
print(data.head())'''

# Convert text into numerical features using TF-IDF

#TF-IDF Object created-responsible for converting text to numbers
#Term Frequency-Inverse Document Frequency
vectorizer=TfidfVectorizer()
X=vectorizer.fit_transform(data['message'])
y=data['label']
'''print("\nShape of TF-IDF Matrix:")
print(X.shape)'''

#Spliting the dataset into training and testing data
#test_size-->percentage of test data 
#random_state-->Every time the data is split, the rows are shuffled.
#ensures the split is the same every time you run the program.
# If don't specify a random_state,will get a different split every time.
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)

print("\nTraining Data Shape:",X_train.shape)
print("Testing Data Shape:",X_test.shape)

#Train Naive Bayes Model
model=MultinomialNB()
#fit()-->trains the machine learning model.It learns patterns from the training
#  data by analyzing the relationship between the TF-IDF features and the corresponding labels.
model.fit(X_train,y_train)
print("\nModel trained successfully!")

#Testing the Model
y_pred=model.predict(X_test)
accuracy=accuracy_score(y_test,y_pred)

print("\nModel Accuracy:")
print(f"{accuracy*100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test,y_pred))

# Save the trained model and TF-IDF vectorizer
joblib.dump(model, "model/spam_model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")

print("\nModel and Vectorizer saved successfully!")