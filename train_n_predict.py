import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Load the dataset from Excel
df = pd.read_excel('source\\model.xlsx')

# Drop rows with NaN values in 'area-muni' or 'address'
df.dropna(subset=['area-muni', 'address'], inplace=True)

# Splitting the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(df['address'], df['area-muni'], test_size=0.2, random_state=42)

# Creating a pipeline with TF-IDF vectorizer and SGDClassifier
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', SGDClassifier(loss='hinge', penalty='l2', random_state=42))
])

# Training the model
pipeline.fit(X_train, y_train)

# Evaluating the model
y_pred = pipeline.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model accuracy: {accuracy}")

# Saving the trained model to a joblib file
joblib.dump(pipeline, 'source\\model.joblib')
print("Model saved to 'model.joblib'")

# Now, to use the trained model to predict area-muni and probability of addresses from an Excel file:
# Load the model
model = joblib.load('source\\model.joblib')

# Assume `addresses.xlsx` contains a column 'address' with the addresses to predict
df_to_predict = pd.read_excel('source\\address.xlsx')

# Drop rows with NaN values in 'address'
df_to_predict.dropna(subset=['address'], inplace=True)
predictions = model.predict(df_to_predict['address'])

# Adding predictions to the DataFrame
df_to_predict['area-muni'] = predictions

# Saving the predictions to a new Excel file
df_to_predict.to_excel('uploads\\predictions.xlsx', index=False)
print("Predictions saved to 'predictions.xlsx'")