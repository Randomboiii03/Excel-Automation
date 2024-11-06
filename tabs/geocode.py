import streamlit as st
import pandas as pd
from datetime import datetime
from time import time
import base64
import uuid
import streamlit.components.v1 as components
from predict import load_model_predict

class Geocode:
    def __init__(self):
        self.geocode_file = None
        self.run()

    def run(self):
        with st.container(border=True):
            st.header('GEOCODE THINGS')
            
            self.geocode_file = st.file_uploader('Choose a XLXS file :red[(Column name must be **\'address\'** - small letter)]', type=['xlsx'], key="geocode_file_uploader")

            geocode_upload_button = st.button('Upload', key="geocode_upload_button")

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
                result_file_path = load_model_predict(self.geocode_file)

                if result_file_path is None:
                    status.update(label=f"Error: Prediction file is None", state="error", expanded=False)
                    st.stop()
                
                # Convert file to base64
                with open(result_file_path, "rb") as result_file:
                    result_byte = result_file.read()
                b64 = base64.b64encode(result_byte).decode()
                
                # Define file name and download function
                current_date = datetime.now().strftime("%m-%d")
                result_file_name = f"GeoResult-{current_date}-{int(time())}.xlsx"

                self.download_base64_file(b64, result_file_name)

                status.update(label=f"Geocoding completed! ", state="complete", expanded=False)
                st.toast('Geocoding Finished!', icon='🎉')
                st.balloons()
                    
            except Exception as e:
                status.update(label=f"Error: {e}", state="error", expanded=False)
                st.snow()

    def download_base64_file(self, b64, download_filename):
        id_link = '_'+str(uuid.uuid4())
        components.html(
            f"""<html><body>                                   
            <a href="data:application/octet-stream;base64,{b64}" download="{download_filename}" id="{id_link}"></a>""" +
            """<script>                                    
                    window.onload = function () {                                            
                        document.getElementById('""" + id_link + """').click();
                                        };                                        
                                    </script>
                                </body></html>                                    
                                """, height=0, width=0)

