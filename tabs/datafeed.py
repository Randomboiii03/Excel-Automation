import streamlit as st
import pandas as pd
from database import DB as db
from train import train_model_save_joblib

class Datafeed:
    def __init__(self):
        with st.container(border=True):
            st.header('DATA FEED THINGS')
            
            self.datafeed_file = st.file_uploader('Choose a XLXS file', type=['xlsx'], key="datafeed_file_uploader")
            
            datafeed_upload_button = st.button('Submit', key="datafeed_upload_button")

            recreate_model_button = st.button('Recreate Model', key="recreate_model_button")

            if datafeed_upload_button:
                if self.datafeed_file is not None:
                    self.feed()
                else:
                    st.toast('Upload File!', icon='❌')

            if recreate_model_button:
                self.recreate_model()



    def recreate_model(self):
        st.toast('Starting Recreating Model', icon='💨')

        st.toast('Don\'t Click Any Button Please...', icon='🙏')

        with st.status("Recreating model...", expanded=True) as status:
            try:
                if not train_model_save_joblib():
                    status.update(label=f"Error: Something went wrong when creating a new model", state="error", expanded=False)
                    st.stop()

                status.update(label=f"Recreating Model completed! ", state="complete", expanded=False)

                st.toast('Recreating Model Finished!', icon='🎉')
                st.balloons()

            except Exception as e:
                status.update(label=f"Error: {e}", state="error", expanded=False)
                st.snow()

    def feed(self):
        st.toast('Starting Data Feeding!', icon='💨')

        st.toast('Don\'t Click Any Button Please...', icon='🙏')

        with st.status("Feeding data to database...", expanded=True) as status:
            try:
                df = pd.read_excel(self.datafeed_file)

                if list(df.columns) != ['area-muni','address']:
                    status.update(label=f":red[**Error:**] Uploaded file has the wrong column format, it must be column: :red[ **area-muni & address**] in small letter ", state="error", expanded=False)
                    st.stop()

                inserted_data = db().insert(df)

                if inserted_data < 0:
                    status.update(label=f":red[**Error:**] Something went wrong with database", state="error", expanded=False)
                    st.stop()
                
                elif inserted_data == 0:
                    status.update(label=f":red[**Error:**] All data is already fed", state="error", expanded=False)
                    st.stop()

                if not train_model_save_joblib():
                    status.update(label=f":red[**Error:**] Something went wrong when creating a new model", state="error", expanded=False)
                    st.stop()

                status.update(label=f"Data Feeding completed! ", state="complete", expanded=False)

                st.toast('Data Feeding Finished!', icon='🎉')
                st.balloons()

            except Exception as e:
                status.update(label=f":red[**Error:**] {e}", state="error", expanded=False)
                st.snow()

    
