import streamlit as st
import pandas as pd

class Map:
    def __init__(self):
        self.config_path = "./source/config.xlsx"
        self.load_config()

        with st.container(border=True):
            st.header('MAP THINGS')

            self.col_header = st.selectbox(
                label="TEMPLATE COLUMN",
                options=self.template_cols,
                key="template_col_selectbox"
            )
            
            self.mappings_value = self.show_mappings_for_selected_template(self.col_header)

            self.new_mapping_value = st.text_area(
                label="MAPPING VALUES :red[(Always in UPPERCASE & use comma - no space between map values)]",
                value=self.mappings_value
            )

            if st.button('Update Config'):
                self.update_config(self.col_header, self.new_mapping_value)

    def load_config(self):
        config_df = pd.read_excel(self.config_path)
        self.template_cols = config_df['TEMPLATE'].tolist()
        self.mappings_cols = config_df['MAPPINGS'].tolist()

    def show_mappings_for_selected_template(self, selected_template):
        
        if selected_template in self.template_cols:
            index = self.template_cols.index(selected_template)
            
            return self.mappings_cols[index]
        return ""

    def update_config(self, template_col, new_mapping_value):
        config_df = pd.read_excel(self.config_path)
        
        index = config_df[config_df['TEMPLATE'] == template_col].index

        if not index.empty:
            index = index[0]

            config_df.at[index, 'MAPPINGS'] = new_mapping_value
            config_df.to_excel(self.config_path, index=False)

            st.toast(f"Config updated for TEMPLATE '**{template_col}**'", icon="✅")

# Instantiate and run the Map class
if __name__ == "__main__":
    Map()
