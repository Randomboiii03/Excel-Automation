import streamlit as st
from tabs import merge, geocode, datafeed

tab1, tab2, tab3 = st.tabs(["📂 MERGE", "🌏 GEOCODE", "🍴 DATA FEED"])

with tab1:
   merge.Merge()

with tab2:
   geocode.Geocode()

with tab3:
   datafeed.Datafeed()