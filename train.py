import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def train_model_save_joblib():
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

if __name__ == "__main__":
    train_model_save_joblib()
