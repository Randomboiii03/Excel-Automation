import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from openpyxl import load_workbook
import functions as func
from time import time
import os

def load_model_predict(file_path):
    try:
        # Now, to use the trained model to predict area-muni and probability of addresses from an Excel file:
        # Load the model
        st.write("Loading predictive model")
        model = joblib.load('source\\model.joblib')

        # Assume `addresses.xlsx` contains a column 'address' with the addresses to predict
        df_to_predict = pd.read_excel(file_path)

        # Drop rows with NaN values in 'address'
        df_to_predict.dropna(subset=['address'], inplace=True)

        st.write("Loading predictive model")
        predictions = model.predict(df_to_predict['address'].astype(str))

        # Convert predictions to a list of tuples
        area_munis = [tuple(prediction.split('-', 1)) for prediction in predictions]

        temp_df = pd.DataFrame()

        temp_df['ADDRESS'] = df_to_predict['address']

        # Adding predictions to the DataFrame
        temp_df['AREA'], temp_df['MUNICIPALITY'] = zip(*area_munis)
        temp_df['FINAL AREA'] = ''
        temp_df['AUTOFIELD DATE'] = ''

        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        
        result_path = f'uploads\\predictions.xlsx'

        # Saving the predictions to a new Excel file
        temp_df.to_excel(result_path, index=False)

        st.write(f"Highlighting predictions")
        func.highlight_n_check_prediction(result_path)

        st.write(f"Autofit columns of excel")
        func.auto_fit_columns(result_path)

        wb = load_workbook(result_path)
        ws = wb.active

        num_columns = ws.max_column

        for row in ws.iter_rows(min_row=1, max_row=1):
            last_cell = row[num_columns - 1]
            ws.delete_cols(last_cell.column, 1)
            ws.delete_cols(last_cell.column -1, 1)
            break
            
        wb.save(result_path)

        print("Predictions saved to 'predictions.xlsx'")
    except Exception as e:
        print(e)
    
    return result_path

if __name__ == "__main__":
    load_model_predict('source\\sample-address.xlsx')
