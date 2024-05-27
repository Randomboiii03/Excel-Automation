import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from openpyxl import load_workbook
import functions as func  # Assuming this is a module you've created
from time import time
import os
from geocode import Geocode  # Assuming this is a module you've created
import sys
from database import DB as db
from threading import Thread
from multiprocessing import Process, Queue
import functions as func
from time import sleep


class Predict():
    def __init__(self):
        # Paths for model and result files
        self.model_path = 'source\\model.joblib'
        self.result_path = 'uploads\\predictions.xlsx'
        
        # Load the ML model
        self.model = joblib.load(self.model_path)

        # Create 'uploads' directory if it doesn't exist
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

    # Method for geocoding using machine learning
    # def with_machine_learning(self, file_path):
        # try:
        #     # Read the Excel file
        #     wb = pd.read_excel(file_path)
        #     existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

        #     # Get a list of addresses with more than 20 characters and not existing
        #     addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna() & (wb['ADDRESS'].str.len() >= 20), 'ADDRESS'].tolist()

        #     prediction_mask = wb['ADDRESS'].isin(addresses)
        #     print(f'Number of addresses to predict: {len(addresses)}')

        #     if len(addresses) > 0:
        #         if addresses:
        #             predictions = self.model.predict(addresses) 
        #         else:
        #             predictions = []

        #         print(f'Number of predictions: {len(predictions)}')  # Debugging line

        #         area_munis = [tuple(prediction.split('-', 1)) for prediction in predictions]
        #         area_munis_bold = [(f'**{area}', f'**{municipality}') for area, municipality in area_munis]
                    
        #         wb.loc[~existing_mask & wb['ADDRESS'].notna() & (wb['ADDRESS'].str.len() >= 20), ['AREA', 'MUNICIPALITY']] = area_munis_bold
        #         wb.to_excel(file_path, index=False)

        # except Exception as e:
        #     print(e)

    def search_address_thread(self, db, address, index, result_queue):
        conn = None
        try:
            # Acquire a connection from the pool
            conn = db.get_connection()
            if conn:
                # Create a cursor object to execute PostgreSQL commands
                cur = conn.cursor()
                result, percentage = db.search_address(address)
                result_queue.put((index, result, percentage))
        finally:
            if conn:
                # Release the connection back to the pool
                db.release_connection(conn)


    def with_database(self, file_path):
        try:
            # Read the Excel file
            wb = pd.read_excel(file_path)

            threads = []
            result_queue = Queue()

            db().create_index()

            for index, row in wb.iterrows():
                area = row['AREA']
                municipality = row['MUNICIPALITY']
                temp = str(row['ADDRESS'])
                address = func.clean_address(temp)

                if pd.isna(area) and pd.isna(municipality) and len(temp) >= 25:
                    print(index, '-', address)
                    thread = Thread(target=self.search_address_thread, args=(db(), address, index, result_queue))
                    thread.start()
                    threads.append(thread)
                    
            # 3:51
            for thread in threads:
                thread.join()

            while not result_queue.empty():
                index, prediction, percentage = result_queue.get()
                print(index, '-', prediction, ':', percentage)
                wb.loc[index, ['AREA', 'MUNICIPALITY']] = tuple(prediction.split('-', 1))
                wb.loc[index, ['PERCENTAGE']] = percentage
                wb.to_excel(file_path, index=False)

        except Exception as e:
            print(e)

            

    # Method for geocoding using JSON data
    def with_json(self, addresses):
        try:
            predictions = []
            print(f'Number of addresses to predict: {len(addresses)}')
            
            geocode = Geocode()  # Assuming this is a class for geocoding
            
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


    # Method to merge geocoded data with the original Excel file
    def merge_it(self, file_path):
        wb = pd.read_excel(file_path)

        existing_mask = (wb['AREA'].notna()) & (wb['MUNICIPALITY'].notna())

        addresses = wb.loc[~existing_mask & wb['ADDRESS'].notna() & (wb['ADDRESS'].str.len() >= 20), 'ADDRESS'].tolist()

        if len(addresses) > 0:
            prediction_mask = wb['ADDRESS'].isin(addresses)
        
            predictions = self.with_json(addresses)

            wb['AREA'] = wb['AREA'].astype(str)
            wb['MUNICIPALITY'] = wb['MUNICIPALITY'].astype(str)

            wb.loc[prediction_mask, ['AREA', 'MUNICIPALITY']] = predictions
            wb.to_excel(file_path, index=False)

            self.with_database(file_path)
                

    # Main method for geocoding only
    def geocode_only(self, file_path):
        wb = pd.read_excel(file_path)

        wb.dropna(subset=['ADDRESS'], inplace=True)
        addresses = wb['ADDRESS'].astype(str)

        # predictions = self.with_json(addresses)
        
        temp_df = pd.DataFrame()

        temp_df['ADDRESS'] = wb['ADDRESS']

        # temp_df['AREA'], temp_df['MUNICIPALITY'] = zip(*predictions)
        temp_df['AREA'], temp_df['MUNICIPALITY'] = ('', '')
        temp_df['PERCENTAGE'] = ''
        
        temp_df.to_excel(self.result_path, index=False)

        self.with_database(self.result_path)

        # func.highlight_n_check_prediction(self.result_path)
        func.auto_fit_columns(self.result_path)
        
        # wb = load_workbook(self.result_path)
        # ws = wb.active

        # num_columns = ws.max_column

        # for row in ws.iter_rows(min_row=1, max_row=1):
        #     last_cell = row[num_columns - 1]
        #     ws.delete_cols(last_cell.column, 1)
        #     ws.delete_cols(last_cell.column -1, 1)
        #     break
            
        # wb.save(self.result_path)

        return self.result_path
        
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python geocode.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(Predict().geocode_only(file_path))
