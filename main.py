import streamlit as st
from tabs import merge, geocode, datafeed, map

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

st.set_page_config(page_title="MergeIT")

tab1, tab2, tab3, tab4 = st.tabs(["📂 MERGE", "🌏 GEOCODE", "🍴 DATA FEED", "🗺️ MAP ME"])

with tab1:
   merge.Merge()

with tab2:
   geocode.Geocode()

with tab3:
   if not st.session_state.authenticated:
        try:
            password = st.text_input("Enter password to access this tab", type="password")
            if password == "21!5)£gEw_|&":  # Replace 'your_password' with the actual password
                st.session_state.authenticated = True
                st.rerun()  # Rerun to hide the password field
            elif password:
                st.error("Incorrect password")
        except Exception as e:
            st.error(f"An error occurred: {e}")
   else:
        try:
            datafeed.Datafeed()
        except Exception as e:
            st.error(f"An error occurred while loading the data feed: {e}")

with tab4:
    map.Map()
