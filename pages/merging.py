import streamlit as st
import functions as func
import pandas as pd
from datetime import datetime
from time import time
import os
import joblib
import uuid
import base64
import streamlit.components.v1 as components
import polars as pl
import numpy as np

class Merging:
    def __init__(self):
        self.main_df = pl.DataFrame()
        self.additional_header = set()
        self.output_file_path = None
    
    def process_files(self, files):
        for file in files:
            index_header = func.get_index_of_header(file, st.session_state.template_cols)
            
            if index_header == -1:
                st.error(f":red[**Error:**] Can\'t find header from {file.name}")
                st.stop()

            sheet_data = pl.read_excel(file, engine='openpyxl')

            if index_header > 0:
                header = list(sheet_data[index_header - 1].row(0)) 
                sheet_data = sheet_data[index_header:]
                sheet_data = sheet_data.rename({col: header[i] if header[i] else '' for i, col in enumerate(sheet_data.columns)})

            sheet_columns = sheet_data.columns

            temp_df = pl.DataFrame(schema=st.session_state.template_cols)
            encoded_columns = set()
            
            for header in st.session_state.template_cols:                
                for col_header in sheet_columns:
                    if f"{col_header} | {file.name}" in st.session_state.selected_values[header]:
                        sheet_data = sheet_data.rename({col_header: header})
                        encoded_columns.add(col_header)
                        break

            temp_df = pl.concat([temp_df, sheet_data], how="diagonal_relaxed")
            
            self.main_df = pl.concat([self.main_df, temp_df], how="diagonal_relaxed")

            st.write(f'**{file.name}** merged :green[successfully] ✅')
    
    def save_and_process(self):
        current_date = datetime.now().strftime("%m-%d")
        
        if not os.path.exists('output'):
            os.makedirs('output')
        
        output_file_name = f"{st.session_state.campaign_name.capitalize()}-{current_date}-{int(time())}.xlsx"
        self.output_file_path = f"./output/{output_file_name}"

        self.main_df = self.main_df.with_columns(pl.col('ADDRESS').str.to_uppercase())

        addresses = pl.Series(self.main_df.with_columns(pl.col('ADDRESS').str.len_chars().alias("n_chars")
                                                        ).filter((pl.col('ADDRESS').is_not_null()) & 
                                                                 (pl.col('n_chars') > 30) &
                                                                 ((pl.col('AREA').is_null()) |
                                                                  (pl.col('MUNICIPALITY').is_null()))
                                                                  ).drop(["n_chars"]).select(pl.col("ADDRESS"))).unique().to_list()
     
        if len(addresses) > 0:
            st.write(f"Number of address to predict: **{len(addresses)}**")
            
            placeholder1 = st.empty()
            placeholder1.text("Loading predictive model 🙉")

            model = joblib.load('./source/model.joblib')

            placeholder1.text("Predictive model loaded ✅")
            
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

            self.main_df = self.main_df.join(area_muni_df, on='ADDRESS', how='left'
                                            ).with_columns([
                                                pl.col('AREA').fill_null(pl.col('AREA_right')), 
                                                pl.col('MUNICIPALITY').fill_null(pl.col('MUNICIPALITY_right'))
                                                ]).drop(['AREA_right', 'MUNICIPALITY_right'])
            
            st.write(f"Number of predicted addresses: **{len(all_predictions)}**")

        else:
            st.write(f"No address to predict ")

        self.main_df = self.main_df.with_columns(pl.sum_horizontal(pl.col('*').is_not_null()).alias("not_null_count")
                                                 ).filter(pl.col("not_null_count") > 1).drop(["not_null_count"])

        self.main_df = func.fill_bank_n_chcode(self.main_df, './source/campaign_list.json')
        
        st.write(f"Creating file temp file 📃")
        self.main_df.write_excel(self.output_file_path, autofit=True)

        output_file = func.highlighting_excel(self.output_file_path)

        placeholder4 = st.empty()
        placeholder4.text(f"Recreating file {output_file_name} 🔃")
        output_file.save(self.output_file_path)
        placeholder4.empty()
        
        st.write(f"File **{output_file_name}** created successfully!")
        
        with open(self.output_file_path, "rb") as file:
            b64 = base64.b64encode(file.read()).decode()

        self.download_base64_file(b64, output_file_name)

    def download_base64_file(self, b64, download_filename):
        id_link = '_'+str(uuid.uuid4())
        components.html(
            f"""<html><body>                                   
            <a href="data:application/pdf;base64,{b64}" download="{download_filename}" id="{id_link}"></a>""" +
            """<script>                                    
                    window.onload = function () {                                            
                        document.getElementById('""" + id_link + """').click();
                                        };                                        
                                    </script>
                                </body></html>                                    
                                """, height=0, width=0)
    
    def run(self):
        if st.button('Back to Main', key='back_to_merge'):
            st.switch_page('main.py')
        
        if st.session_state.merge_files:
            with st.container(border=True):
                st.header("DOING THINGS")
                
                with st.status("Merging excels...", expanded=True) as status:
                    try:
                        self.process_files(st.session_state.merge_files)
                        self.save_and_process()

                        st.balloons()

                        status.update(label=f"Merging successfully :green[completed]! ", state="complete", expanded=False)
                    except Exception as e:
                        status.update(label=f":red[**Error:**] {e}", state="error", expanded=False)
                        st.snow()

                        st.button('Refresh')

                    finally:
                        if self.output_file_path:
                            os.remove(self.output_file_path)

            # st.json(st.session_state.selected_values, expanded=False)

        else:
            st.switch_page('main.py')

# Run the Merging process
merging = Merging()
merging.run()
