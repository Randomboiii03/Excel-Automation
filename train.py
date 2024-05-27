import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
from database import DB as db
import functions as func

def train_model_save_joblib():
    try:        
        print("Fetching data")
        area_munis, addresses = db().select()
        print(area_munis, addresses)
        # db().close()

        if area_munis is None and addresses is None:
            return False

        addresses = [func.clean_address(address) for address in addresses]

        model_names = ["area_model", "muni_model"]
        temp = [tuple(area_muni.split('-', 1)) for area_muni in area_munis]

        area, muni = zip(*temp)

        for index, model_name in enumerate(model_names):
            print("Splitting...")
            # Splitting the data into training and test sets
            X_train, X_test, y_train, y_test = train_test_split(addresses, area if index == 0 else muni, test_size=0.2, random_state=42)

            print("Setting pipeline...")
            # Creating a pipeline with TF-IDF vectorizer and SGDClassifier
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer()),
                ('clf', SGDClassifier(loss='hinge', penalty='l2', random_state=42))
            ])
            
            print("Start training...")
            # Training the model
            pipeline.fit(X_train, y_train)
            
            # Evaluating the model
            # y_pred = pipeline.predict(X_test)
            # accuracy = accuracy_score(y_test, y_pred)
            # print(f"Model accuracy: {accuracy}")
            
            # Saving the trained model to a joblib file
            joblib.dump(pipeline, f'./source/{model_name}.joblib')
            print(f"Model saved to '{model_name}.joblib'")

        return True
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    train_model_save_joblib()
