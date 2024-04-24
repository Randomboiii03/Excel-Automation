import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from openpyxl import load_workbook
import functions as func
from time import time
import os
from geocode import Geocode
import sys


class Predict():
    def __init__(self):
        self.model_path = 'source\\model.joblib'
        self.result_path = 'uploads\\predictions.xlsx'
        
        self.model = joblib.load(self.model_path)

        if not os.path.exists('uploads'):
            os.makedirs('uploads')

    def with_machine_learning(self, file_path):
        try:
            wb = pd.read_excel(file_path)
            existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

            addresses = wb.loc[~existing_mask, 'ADDRESS'].tolist()
            addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna(), 'ADDRESS'].tolist()

            prediction_mask = wb['ADDRESS'].isin(addresses)
            print(f'Number of addresses to predict: {len(addresses)}')

            if len(addresses) > 0:
                if addresses:
                    predictions = self.model.predict(addresses) 
                else:
                    predictions = []

                print(f'Number of predictions: {len(predictions)}')  # Debugging line

                area_munis = [tuple(prediction.split('-', 1)) for prediction in predictions]
                area_munis_bold = [(f'**{area}', f'**{municipality}') for area, municipality in area_munis]
                    
                wb.loc[~existing_mask & wb['ADDRESS'].notna(), ['AREA', 'MUNICIPALITY']] = area_munis_bold
                wb.to_excel(file_path, index=False)

        except Exception as e:
            print(e)
            

    def with_json(self, addresses):
        try:
            predictions = []
            print(f'Number of addresses to predict: {len(addresses)}')
            
            geocode = Geocode()
            
            for address in addresses:
                result = geocode.search(str(address))
                
                if result:
                    predictions.append(result)
                else:
                    predictions.append(['', ''])

            print(f"NOT FOUND: {geocode.count_not_found}")

            return predictions
        except Exception as e:
            print(e)


    def merge_it(self, file_path):
        wb = pd.read_excel(file_path)

        existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

        addresses = wb.loc[~existing_mask, 'ADDRESS'].tolist()
        addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna(), 'ADDRESS'].tolist()

        prediction_mask = wb['ADDRESS'].isin(addresses)
        
        predictions = self.with_json(addresses)

        wb['AREA'] = wb['AREA'].astype(str)
        wb['MUNICIPALITY'] = wb['MUNICIPALITY'].astype(str)

        wb.loc[prediction_mask, ['AREA', 'MUNICIPALITY']] = predictions
        wb.to_excel(file_path, index=False)

        self.with_machine_learning(file_path)
                

    def geocode_only(self, file_path):
        wb = pd.read_excel(file_path)

        wb.dropna(subset=['ADDRESS'], inplace=True)
        addresses = wb['ADDRESS'].astype(str)

        predictions = self.with_json(addresses)
        
        temp_df = pd.DataFrame()

        temp_df['ADDRESS'] = wb['ADDRESS']

        temp_df['AREA'], temp_df['MUNICIPALITY'] = zip(*predictions)
        temp_df['FINAL AREA'] = ''
        temp_df['AUTOFIELD DATE'] = ''
        
        temp_df.to_excel(self.result_path, index=False)

        self.with_machine_learning(self.result_path)

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

        return self.result_path
        
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python geocode.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(Predict().geocode_only(file_path))