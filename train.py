# import pandas as pd
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.ensemble import RandomForestClassifier
# from joblib import dump

# # Step 1: Load the source data
# source_data = pd.read_excel('model.xlsx')

# # Step 2: Preprocess the source data
# source_addresses = source_data['address'].fillna('').values
# source_muni_areas = source_data['area-muni'].fillna('').values

# # Step 3: Train the machine learning model
# vectorizer = CountVectorizer(sparse=True)  # Specify sparse=True for sparse matrix
# source_vectorized = vectorizer.fit_transform(source_addresses)
# model = RandomForestClassifier()
# model.fit(source_vectorized, source_muni_areas)

# # Step 4: Save the trained model
# dump(model, 'model.joblib')

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
import joblib
import numpy as np

def train_model_save_joblib():
    # Step 1: Load the source data
    source_data = pd.read_excel('model.xlsx')  # Assuming the data is in Excel format

    # Step 2: Preprocess the source data
    source_addresses = source_data['address'].fillna('').values
    source_muni_areas = source_data['area-muni'].fillna('').values

    # Step 3: Train the machine learning model
    vectorizer = CountVectorizer()
    source_vectorized = vectorizer.fit_transform(source_addresses)

    # Sample a subset of the data
    sample_indices = np.random.choice(source_vectorized.shape[0], size=min(10000, source_vectorized.shape[0]), replace=False)
    source_vectorized_sampled = source_vectorized[sample_indices]
    source_muni_areas_sampled = source_muni_areas[sample_indices]

    # Train the machine learning model on the sampled data
    model = SGDClassifier(loss='log_loss', max_iter=1000, tol=1e-3, random_state=42)  # Using logistic regression with SGD
    model.partial_fit(source_vectorized_sampled, source_muni_areas_sampled, classes=np.unique(source_muni_areas))

    # Save the trained model using joblib
    joblib.dump(model, 'trained_model.joblib')
    joblib.dump(vectorizer, 'vectorizer.joblib')

    print("Model training and saving completed.")

if __name__ == "__main__":
    train_model_save_joblib()
