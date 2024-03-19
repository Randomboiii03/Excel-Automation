import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

def load_model_predict(file_path):
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

    result_path = 'uploads\\predictions.xlsx'

    # Saving the predictions to a new Excel file
    df_to_predict.to_excel(result_path, index=False)
    print("Predictions saved to 'predictions.xlsx'")
    
    return result_path

if __name__ == "__main__":
    load_model_predict()
