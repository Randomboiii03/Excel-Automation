import pandas as pd
import joblib
from openpyxl import load_workbook
import functions as func
import os
import streamlit as st
import polars as pl
import numpy as np

def load_model_predict(file_path):
    result_path = None

    try:
        placeholder1 = st.empty()
        placeholder1.text("Loading predictive model 🙉")

        model = joblib.load('./source/model.joblib')

        placeholder1.text("Predictive model loaded ✅")

        df_to_predict = pl.read_excel(file_path, engine='openpyxl')
            
        try:
            addresses = pl.Series(df_to_predict.with_columns(pl.col('address').str.len_chars().alias("n_chars")
                                                            ).filter(
                                                                (pl.col('address').is_not_null()) &
                                                                (pl.col('n_chars') > 18)
                                                                ).drop('n_chars').select(pl.col('address'))).unique().to_list()
        except:
            st.write(":red[**Error:**] 'address' column not found in the file.")    
            return result_path
            
        df_to_predict = df_to_predict.rename({'address': 'ADDRESS'})
        
        temp_df = pl.DataFrame(schema=['ADDRESS', 'AREA', 'MUNICIPALITY'])
        temp_df = pl.concat([temp_df, df_to_predict], how="diagonal_relaxed")
        
        if len(addresses) > 0:
            st.write(f"Number of addresses to predict: **{len(addresses)}**")

            batch_size = 10000
            all_predictions = []
            num_batches = int(np.ceil(len(addresses) / batch_size))

            placeholder2 = st.empty()

            for i, start in enumerate(range(0, len(addresses), batch_size)):
                end = min(start + batch_size, len(addresses))
                batch_addresses = addresses[start:end]

                placeholder2.text(f"Processing batch {i + 1} of {num_batches}...")

                try:
                    batch_predictions = model.predict(batch_addresses)
                    batch_area_munis = [tuple(prediction.split('-', 1)) for prediction in batch_predictions]
                    all_predictions.extend(batch_area_munis)
                except Exception as e:
                    st.write(f":red[**Error:**] Prediction failed for batch starting at index {start}: {e}")
                    continue

            area_muni_df = pl.DataFrame(all_predictions, schema=["AREA", "MUNICIPALITY"]).insert_column(0, pl.Series("ADDRESS", addresses))

            temp_df = temp_df.join(area_muni_df, on='ADDRESS', how='left'
                                            ).with_columns([
                                                pl.col('AREA').fill_null(pl.col('AREA_right')), 
                                                pl.col('MUNICIPALITY').fill_null(pl.col('MUNICIPALITY_right'))
                                                ]).drop(['AREA_right', 'MUNICIPALITY_right'])
            
            st.write(f"Number of predicted addresses: **{len(all_predictions)}**")

        else:
            st.write(f"No address to predict ❌")
        
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        
        result_path = 'uploads/predictions.xlsx'
        st.write(f"Creating file temp file 📃")
        temp_df.write_excel(result_path, autofit=True)

        output_file = func.highlighting_excel(result_path, "geocode")
        
        placeholder3 = st.empty()
        placeholder3.text(f"Recreating file {result_path} 🔃")
        output_file.save(result_path)

        return result_path

    except Exception as e:
        st.write(f":red[**Error:**] {str(e)}")
        return None

        

if __name__ == "__main__":
    load_model_predict('source/sample-address.xlsx')
