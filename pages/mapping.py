import streamlit as st
import pandas as pd
import functions as func

class Mapping:
    def __init__(self):
        self.config_path = "./source/config.xlsx"
        self.load_config()

        if st.button('Back to', key='back_to_merge'):
            st.switch_page('main.py')

        if 'campaign_name' in st.session_state or 'merge_files' in st.session_state:
            with st.form(key='mapped', border=True):
                st.header('MAPPING THINGS')

                self.all_columns = self.get_columns()
                all_options = self.create_file_column_list()
                st.session_state.all_options = all_options

                # Initialize session state variables if they do not exist
                if 'selected_values' not in st.session_state:
                    st.session_state.selected_values = {}
                if 'new_options' not in st.session_state:
                    st.session_state.new_options = {}
                if 'default_values' not in st.session_state:
                    st.session_state.default_values = {}
                if 'file_to_map' not in st.session_state:
                    st.session_state.file_to_map = {}

                for template, mappings in zip(self.template_cols, self.mappings_cols):
                    self.update_options(template, mappings)

                    if st.session_state.file_to_map[template] > 0:
                        options = st.multiselect(
                            label=f"**{template}** - :red[**{st.session_state.file_to_map[template]} FILE/S**]",
                            options=st.session_state.new_options[template],
                            key=template
                        )

                        st.session_state.selected_values[template] = options + st.session_state.default_values.get(template, [])

                    else:
                        st.session_state.selected_values[template] = st.session_state.default_values.get(template, [])

                    if len(st.session_state.selected_values[template]) >= len(st.session_state.merge_files) and st.session_state.file_to_map[template] <= 0:
                        st.write(f":green[**{template}**] is already MAPPED ✅")

                if st.form_submit_button('Start'):
                    st.session_state.selected_values = {k: list(set(v)) for k, v in st.session_state.selected_values.items()}  # Remove duplicates
                    st.switch_page('pages/merging.py')
        else:
            st.switch_page('main.py')

    def load_config(self):
        config_df = pd.read_excel(self.config_path)
        self.template_cols = config_df['TEMPLATE'].tolist()
        self.mappings_cols = config_df['MAPPINGS'].tolist()

        st.session_state.template_cols = self.template_cols

    def get_columns(self):
        dict_uploaded_cols = {}
        for uploaded_file in st.session_state.merge_files:
            index_header = func.get_index_of_header(uploaded_file, self.template_cols)

            if index_header == -1:
                st.toast(f'Process stopped, can\'t find header of {uploaded_file.name}', icon='🙏')
                st.stop()

            sheet_data = pd.read_excel(uploaded_file, sheet_name=0, header=index_header)
            dict_uploaded_cols[uploaded_file.name] = sheet_data.columns.tolist()

        return dict_uploaded_cols

    def create_file_column_list(self):
        return [f"{column} | {file_name}" for file_name, columns in self.all_columns.items() for column in columns]

    def update_options(self, template, mappings):
        selected_options = [opt for opt in st.session_state.all_options if func.clean_string(opt.split(' | ')[0]) in mappings.split(',')]
        excluded_options = [item for item in st.session_state.all_options 
                            if item.split(' | ')[1] not in [opt.split(' | ')[1] for opt in selected_options] and 
                            func.clean_string(item.split(' | ')[0]) not in [m for mapping in self.mappings_cols for m in mapping.split(',')]]
        
        st.session_state.new_options[template] = excluded_options
        st.session_state.default_values[template] = selected_options
        st.session_state.file_to_map[template] = len(set([opt.split(' | ')[1] for opt in excluded_options]))

Mapping()
