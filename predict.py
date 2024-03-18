import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import os

def load_model_predict(file_path):
    # Load the trained model using joblib
    model = joblib.load('source\\trained_model.joblib')

    # Step 1: Load the uploaded data
    uploaded_data = pd.read_excel(file_path)  # Assuming the data is in Excel format

    # Step 2: Preprocess the uploaded data
    uploaded_addresses = uploaded_data['address'].fillna('').values

    # Step 3: Load the CountVectorizer used for training
    vectorizer = CountVectorizer()
    vectorizer = joblib.load('source\\vectorizer.joblib')

    # Step 4: Transform the uploaded addresses using the loaded CountVectorizer
    uploaded_vectorized = vectorizer.transform(uploaded_addresses)

    # Step 5: Predict the muni-area and obtain probability estimates for the uploaded addresses
    predictions = model.predict(uploaded_vectorized)
    probabilities = model.predict_proba(uploaded_vectorized)

    # Step 6: Create the result DataFrame
    result_data = pd.DataFrame({
        'Address': uploaded_data['address'],
        'Muni-Area': predictions
    })

    new_probability = []
    prob_columns = model.classes_

    for index, muni_area in enumerate(result_data['Muni-Area']):
        if muni_area in prob_columns:
            new_probability.append(probabilities[index][np.where(prob_columns == muni_area)])

    prob_data = pd.DataFrame(new_probability, columns=['Probability'])
    result_data = pd.concat([result_data, prob_data], axis=1)

    result_path = os.path.join("uploads",'result.xlsx')

    # Step 7: Save the result DataFrame to a new Excel file
    result_data.to_excel(result_path, index=False)

    print("Prediction completed and result saved.")
    
    return result_path

if __name__ == "__main__":
    load_model_predict()
