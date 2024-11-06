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

            campaign_name = st.text_input("Campaign Name")
            merge_files = st.file_uploader('Choose a XLXS file', accept_multiple_files=True, type=['xlsx'], key="merge_file_uploader")

            merge_upload_button = st.button('Upload', key="merge_upload_button")

        if merge_upload_button:
            if len(merge_files) > 0 and campaign_name:
                st.session_state.campaign_name = campaign_name
                st.session_state.merge_files = merge_files

                st.switch_page('pages/mapping.py')
            elif not campaign_name:
                st.warning('Fill campaign name!', icon="⚠️")
            else:
                st.warning('Upload file first!', icon="⚠️")
