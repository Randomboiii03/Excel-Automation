import streamlit as st
from predict import load_model_predict
import pandas as pd
from datetime import datetime
from time import sleep, time

class Geocode:
    def __init__(self):
        with st.form('geocode_form'):
            st.header('GEOCODE THINGS')
            
            self.geocode_file = st.file_uploader('Choose a XLXS file', type=['xlsx'])

            geocode_upload_button = st.form_submit_button('Upload')

            if geocode_upload_button:
                if self.geocode_file is not None:
                    self.geocode()
                else:
                    st.toast('Upload File!', icon='❌')

    def geocode(self):
        st.toast('Starting Geocoding!', icon='💨')

        st.toast('Don\'t Click Any Button Please...', icon='🙏')

        with st.status("Geocoding excel...", expanded=True) as status:
            try:
                result_file_path = load_model_predict(file_path)
                
                with open(result_file_path, "rb") as result_file:
                    result_byte = result_file.read()

                current_date = datetime.now().strftime("%Y-%m-%d")

                result_file_name = f"Geocode_result-{current_date}-{int(time())}.xlsx"
                    
                if st.download_button(label='Download Output', data=result_byte, file_name=result_file_name, mime="application/octet-stream", key="result_file"):
                    st.toast(f'{result_file_name} Downloaded!', icon='📥')

                status.update(label=f"Geocoding completed! ", state="complete", expanded=False)

                st.toast('Geocoding Finished!', icon='🎉')
                st.balloons()
                    
            except Exception as e:
                status.update(label=f"Error: {e}", state="error", expanded=False)
                st.snow()

        