import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from openpyxl import load_workbook
import functions as func
from time import time
import os
from geocode import Geocode


class Predict():
    def __init__(self, file_path, merge=True):
        self.file_path = file_path
        self.model_path = 'source\\model.joblib'
        self.result_path = 'uploads\\predictions.xlsx'
        self.merge = merge

        self.model = joblib.load(self.model_path)

        if not os.path.exists('uploads'):
            os.makedirs('uploads')

    def with_machine_learning(self):
        try:
            wb = pd.read_excel(self.file_path)
            existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

            addresses = wb.loc[~existing_mask, 'ADDRESS'].tolist()
            addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna(), 'ADDRESS'].tolist()

            prediction_mask = wb['ADDRESS'].isin(addresses)
            print(f'Number of addresses to predict: {len(addresses)}')

            if addresses:
                predictions = self.model.predict(addresses) 
            else:
                predictions = []

            print(f'Number of predictions: {len(predictions)}')  # Debugging line
            
            area_munis = [tuple(prediction.split('-', 1)) for prediction in predictions]
            
            wb.loc[prediction_mask, 'AREA'], wb.loc[prediction_mask, 'MUNICIPALITY'] = zip(*area_munis)
            
            wb.to_excel(self.file_path, index=False)

        except Exception as e:
            print(e)
            

    def with_json(self):
        wb = pd.read_excel(self.file_path)

        addresses = []
        
        if self.merge:
            existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

            addresses = wb.loc[~existing_mask, 'ADDRESS'].tolist()
            addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna(), 'ADDRESS'].tolist()

            prediction_mask = wb['ADDRESS'].isin(addresses)

        else:
            wb.dropna(subset=['ADDRESS'], inplace=True)
            addresses = wb['ADDRESS'].astype(str)
        
        print(f'Number of addresses to predict: {len(addresses)}')

        geocode = Geocode()
        predictions = []
        
        for address in addresses:
            result = geocode.search(str(address))

            if result:
                predictions.append(result)
            else:
                predictions.append(['', ''])

        print(f"NOT FOUND: {geocode.count_not_found}")

        if self.merge:
            wb.loc[prediction_mask, 'AREA'], wb.loc[prediction_mask, 'MUNICIPALITY'] = zip(*predictions)
            wb.to_excel(self.file_path, index=False)

        else:
            temp_df = pd.DataFrame()

            temp_df['ADDRESS'] = wb['ADDRESS']

            temp_df['AREA'], temp_df['MUNICIPALITY'] = zip(*predictions)
            temp_df['FINAL AREA'] = ''
            temp_df['AUTOFIELD DATE'] = ''

            temp_df.to_excel(self.result_path, index=False)

            self.file_path = self.result_path

    def main(self):
        self.with_json()
        self.with_machine_learning()

        func.highlight_n_check_prediction(self.result_path)
        func.auto_fit_columns(self.result_path)

        wb = load_workbook(self.result_path)
        ws = wb.active

        num_columns = ws.max_column

        for row in ws.iter_rows(min_row=1, max_row=1):
            last_cell = row[num_columns - 1]
            ws.delete_cols(last_cell.column, 1)
            ws.delete_cols(last_cell.column -1, 1)
            break
                
        wb.save(self.result_path)

        print("FINISHED")

        return self.result_path

if __name__ == "__main__":
    Predict('WITHOUT AI.xlsx', False).main()

