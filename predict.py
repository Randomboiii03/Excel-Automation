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
    def __init__(self, file_path):
        self.file_path = file_path
        self.model_path = 'source\\model.joblib'
        self.result_path = 'uploads\\predictions.xlsx'

        self.model = joblib.load(self.model_path)

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
        existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

        addresses = wb.loc[~existing_mask, 'ADDRESS'].tolist()
        addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna(), 'ADDRESS'].tolist()

        prediction_mask = wb['ADDRESS'].isin(addresses)
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

        wb.loc[prediction_mask, 'AREA'], wb.loc[prediction_mask, 'MUNICIPALITY'] = zip(*predictions)
        wb.to_excel(self.file_path, index=False)


    def main(self):
        print('PREDICTING WITH JSON..')
        self.with_json()

        print('PREDICTING WITH ML..')
        self.with_machine_learning()


if __name__ == "__main__":
    Predict('WITHOUT AI.xlsx').main()
