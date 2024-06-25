import streamlit as st
from datetime import datetime
from time import sleep, time
import functions as func
import base64
import os
from database import DB as db
import pandas as pd
import joblib

class Merge:
    def __init__(self):
        db().create()

        with st.container(border=True):
            st.header('MERGE THINGS')

            self.campaign_name = st.text_input("Campaign Name")
            self.merge_files = st.file_uploader('Choose a XLXS file', accept_multiple_files=True, type=['xlsx'])

            count = 0

            for uploaded_file in self.merge_files:
                count += 1

            merge_upload_button = st.button('Upload', key="merge_upload_button")

            if merge_upload_button:
                if count > 0 and self.campaign_name:
                    self.upload_files()
                elif not self.campaign_name:
                    st.warning('Fill campaign name!', icon="⚠️")
                else:
                    st.warning('Upload file first!', icon="⚠️")

        with open("./source/templates/template.xlsx", "rb") as template_file:
            template_byte = template_file.read()
            
        if st.download_button(label='Download Template', data=template_byte, file_name="merge_template.xlsx", mime="application/octet-stream", key="merge_template"):
            st.toast('Template Downloaded!', icon='📥')

        self.is_complete = False
            
    def upload_files(self):
        st.toast('Starting Merging!', icon='💨')

        st.toast('Don\'t Click Any Button Please...', icon='🙏')

        self.merge()

        st.toast('Merging Finished!', icon='🎉')

    def merge(self):
        output_file_path = None

        with st.status("Merging excels...", expanded=True) as status:
            try:
                template_path = "./source/templates/template.xlsx"

                template_header = pd.read_excel(template_path).columns.to_list()

                mapping = {
                    "ADDRESS TYPE": "ADD TYPE",
                    "ADD": "ADDRESS",
                    "REQUEST DATE": "DATE REQUESTED",
                    "REQUEST NAME": "REQUESTED BY",
                    "DATE": "DATE REQUESTED"
                    # Add more mappings as needed
                }

                main_df = pd.DataFrame()
                additional_header = set()

                for uploaded_file in self.merge_files:            
                    index_header = func.get_index_of_header(uploaded_file, template_header)

                    if index_header == -1:
                        status.update(label=f"Error: Can\'t find header from {uploaded_file.name}", state="error", expanded=False)
                        st.stop()

                    sheet_data = pd.read_excel(uploaded_file, sheet_name=0, header=index_header)

                    sheet_columns = sheet_data.columns.to_list()
                    
                    temp_df = pd.DataFrame()
                    encoded_columns = set()
                    
                    for header in template_header:
                        isIn = False

                        for col_header in sheet_columns:
                            if header == func.map_header(mapping, col_header):
                                temp_df[func.map_header(mapping, col_header)] = sheet_data[col_header].copy()
                                encoded_columns.add(col_header)
                                isIn = True
                                break

                            elif func.compare_string(header, col_header):
                                temp_df[header] = sheet_data[col_header].copy()
                                encoded_columns.add(col_header)
                                isIn = True
                                break

                        if not isIn:
                            temp_df[header] = ''
                    
                    not_encoded_columns = [x for x in sheet_columns if x not in encoded_columns]
                    
                    for col_header in not_encoded_columns:
                        isIn = False
                        
                        for header in additional_header:
                            if func.compare_string(header, col_header):
                                temp_df[header] = sheet_data[col_header].copy()
                                isIn = True
                                break
                            
                        if not isIn and "UNNAMED" not in func.clean_string(col_header) and not func.is_empty_or_spaces(col_header):
                            temp_df[func.clean_string(col_header).strip()] = sheet_data[col_header].copy()
                            additional_header.add(func.clean_string(col_header))


                    main_df = pd.concat([main_df, temp_df], ignore_index=True)

                    st.write(f'{uploaded_file.name} merged successfully')
                    
                current_date = datetime.now().strftime("%Y-%m-%d")

                if not os.path.exists('output'):
                    os.makedirs('output')
                
                output_file_name = f"Output-{self.campaign_name}-{current_date}-{int(time())}.xlsx"
                output_file_path = f"./output/{output_file_name}"

                main_df.to_excel(output_file_path, index=False)

                st.write(f"Creating file {output_file_name}")

                main_df['ADDRESS'] = main_df['ADDRESS'].str.upper()

                existing_mask = (main_df['AREA'].notna()) & (main_df['MUNICIPALITY'].notna()) & (main_df['MUNICIPALITY'].isna()) & (main_df['AREA'].isna())
                
                addresses = main_df.loc[~existing_mask & main_df['ADDRESS'].notna() & (main_df['ADDRESS'].str.len() >= 20), 'ADDRESS'].tolist()

                if len(addresses) > 0:
                    st.write(f"Number of address to predict: {len(addresses)}")

                    st.write("Loading predictive model")
                    model = joblib.load('./source/model.joblib')
                    
                    prediction_mask = main_df['ADDRESS'].isin(addresses)
                    predictions = model.predict(addresses) 
                    
                    st.write(f"Number of predicted addresses: {len(predictions)}")

                    area_munis = [tuple(prediction.split('-', 1)) for prediction in predictions]

                    main_df.loc[prediction_mask, 'AREA'], main_df.loc[prediction_mask, 'MUNICIPALITY'] = zip(*area_munis)

                else:
                    st.write(f"No address to predict")
            
                main_df.to_excel(output_file_path, index=False)

                func.drop_row_with_one_cell(output_file_path)

                st.write(f"Checking CHCODE and Campaign")
                func.highlight_n_fill_missing_values(output_file_path, './source/campaign_list.json' )

                st.write(f"Highlighting predictions")
                func.highlight_n_check_prediction(output_file_path)

                st.write(f"Autofit columns of excel")
                func.auto_fit_columns(output_file_path)

                with open(output_file_path, "rb") as output_file:
                    output_byte = output_file.read()
                    
                if st.download_button(label='Download Output', data=output_byte, file_name=output_file_name, mime="application/octet-stream", key="output_file"):
                    st.toast(f'{output_file_name} Downloaded!', icon='📥')

                status.update(label=f"Merging completed! ", state="complete", expanded=False)
                st.balloons()

            except Exception as e:
                status.update(label=f"Error: {e}", state="error", expanded=False)
                st.snow()

                if output_file_path:
                    os.remove(output_file_path)