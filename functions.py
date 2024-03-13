from fuzzywuzzy import fuzz
import json
import re
from openpyxl.styles import PatternFill, Font
from openpyxl import load_workbook
import pandas as pd
import os

# Function to get header from an Excel file
def get_template_header(file_path):
    return pd.read_excel(file_path).columns.astype(str).str.upper().to_list()

# Function to get the total number of rows in an Excel file
def get_total_rows(file_path):
    xls = pd.ExcelFile(file_path)
    total_rows = 0

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name)
        total_rows += df.shape[0]

    return total_rows

# Function to compare two strings with a given threshold using fuzzy matching
def compare_string(str1, str2, threshold=90):
    similarity_ratio = fuzz.token_set_ratio(str(str1).lower(), str(str2).lower())
    return similarity_ratio >= threshold

# Function to find a header in a list of row values
def find_header(row_values, template_header):
    row_list = row_values.tolist()
    for header in template_header:
        for data in row_list:
            if compare_string(data, header):
                return True
    return False

# Function to get the index of the header in an Excel file
def get_index_of_header(excel_file_path, template_header) -> int:
    work_book = pd.read_excel(excel_file_path, sheet_name=None, header=None)
    for _, sheet_data in work_book.items():
        if sheet_data.empty:
            return 0
        for index, row in sheet_data.iterrows():
            if find_header(row.values, template_header):
                return index
    return 0

# Function to map a header based on a given mapping dictionary
def map_header(header, mapping):
    for key, value in mapping.items():
        if compare_string(header.lower(), key.lower()):
            return value
    return header

# Function to highlight and fill missing values in specific columns
def highlight_n_fill_missing_values(excel_file_path, campaign_file_path):
    with open(campaign_file_path, 'r') as file:
        campaign_data = json.load(file)

    df = pd.read_excel(excel_file_path)
    
    # Convert CH CODE to string
    df['CH CODE'] = df['CH CODE'].astype(str)

    # Load the workbook
    book = load_workbook(excel_file_path)

    # Access the active sheet
    sheet = book.active

    column_headers = ['BANK', 'PLACEMENT']

    def process_column(column_name):
        if pd.isna(row[column_name]):
            column_index = df.columns.get_loc(column_name) + 1
            cell = sheet.cell(row=row_index + 2, column=column_index)

            ch_code_match = re.search(r'^(\d+[A-Z]+)', str(row['CH CODE']))  # Extract first numbers and letters from CH CODE

            if ch_code_match is not None:
                ch_code = ch_code_match.group(1)
                if ch_code in campaign_data:
                    cell.value = campaign_data[ch_code][column_name]
                else:
                    cell.fill = PatternFill(start_color="FFD3D3", end_color="FFD3D3", fill_type="solid")

    # Apply cell styling for each header cell
    for row_index, row in df.iterrows():
        for header in column_headers:
            process_column(header)

    # Save the workbook
    book.save(excel_file_path)

# Function to drop rows with CH CODE that has all-letter value
def drop_row_with_one_cell(excel_file_path):
    excel_data = pd.read_excel(excel_file_path)

    # Convert CH CODE to string
    excel_data['CH CODE'] = excel_data['CH CODE'].astype(str)
    # Drop rows with CH CODE that has all-letter value
    excel_data = excel_data[~excel_data['CH CODE'].str.isalpha()]
    
    # Save the modified DataFrame to an Excel file
    excel_data.to_excel(excel_file_path, index=False)

# Function to extract and save address data from an output Excel file
def extract_address(output_file_path, address_column_name, output_address_file_path):
    output_data = pd.read_excel(output_file_path)
    address_data = output_data[address_column_name].dropna()
    address_data.to_excel(output_address_file_path, index=False)

# Function to auto-fit columns in an Excel file
def auto_fit_columns(excel_file_path):
    wb = load_workbook(excel_file_path)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]

        for column_cells in ws.columns:
            # Apply style to the header cells
            header_fill = PatternFill(start_color="D4AC0D", end_color="D4AC0D", fill_type="solid")  # Gray color
            header_font = Font(bold=True)

            for cell in column_cells:
                if cell.row == 1:  # Assuming header is in the first row
                    cell.fill = header_fill
                    cell.font = header_font
                    # Convert header text to uppercase
                    cell.value = str(cell.value).upper()

            # Auto-fit column width
            max_length = max(len(str(cell.value)) for cell in column_cells)
            adjusted_width = (max_length + 2) * 1.2  # Adjusted width with a factor for padding
            ws.column_dimensions[column_cells[0].column_letter].width = adjusted_width

    # Save the workbook
    wb.save(excel_file_path)

# Function to delete all downloaded request files
def delete_requests_file(folder_path):
    files_to_delete = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        os.remove(file_path)