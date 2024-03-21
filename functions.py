      
from fuzzywuzzy import fuzz
import json
import re
from openpyxl.styles import PatternFill, Font
from openpyxl import load_workbook
import pandas as pd
import os

def get_headers(file_path):
    return pd.read_excel(file_path).columns.to_list()

def get_total_rows(file_path):
    workbook = load_workbook(file_path)
    worksheet = workbook.active
    total_rows = worksheet.max_row
    return total_rows

def clean_string(input_string):
    return re.sub(r'[^a-zA-Z0-9\s]', ' ', input_string).upper()

def is_empty_or_spaces(s):
    return s.replace(' ', '') == ''

def compare_string(str1, str2, threshold=90):
    similarity_ratio = fuzz.token_set_ratio(clean_string(str(str1)).lower(), clean_string(str(str2)).lower())
    return similarity_ratio >= threshold

def find_header(row_values, template_header):
    for data in row_values:
        for header in template_header:
            if compare_string(data, header):
                return True
    return False

def get_index_of_header(excel_file_path, template_header) -> int:
    sheet_data = pd.read_excel(excel_file_path, sheet_name=0, header=None)
    if sheet_data.empty:
        return 0
    cleaned_template_header = clean_string(template_header)
    header_found = sheet_data.apply(lambda row: find_header(row.values, cleaned_template_header), axis=1)
    index = header_found.idxmax() if header_found.any() else 0
    return index

def map_header(mapping, header):
    cleaned_header = clean_string(header)
    return mapping.get(cleaned_header, None)

def highlight_n_fill_missing_values(excel_file_path, campaign_file_path):
    with open(campaign_file_path, 'r') as file:
        campaign_data = json.load(file)
        
    df = pd.read_excel(excel_file_path)
    
    df['CH CODE'] = df['CH CODE'].astype(str)
    
    book = load_workbook(excel_file_path)
    sheet = book.active
    
    column_headers = ['BANK', 'PLACEMENT']
    
    def process_column(column_name, row):
        if pd.isna(row[column_name]):
            ch_code_match = re.search(r'^(\d+[A-Z]+)', str(row['CH CODE']))
            if ch_code_match is not None:
                ch_code = ch_code_match.group(1)
                if ch_code in campaign_data:
                    return campaign_data[ch_code][column_name]
                else:
                    return None
        return row[column_name]
    
    for row_index, row in df.iterrows():
        for header in column_headers:
            column_index = df.columns.get_loc(header) + 1
            cell = sheet.cell(row=row_index + 2, column=column_index)
            cell_value = process_column(header, row)
            if cell_value is None:
                cell.fill = PatternFill(start_color="FFD3D3", end_color="FFD3D3", fill_type="solid")
            else:
                cell.value = cell_value
                
    book.save(excel_file_path)

def drop_row_with_one_cell(excel_file_path):
    excel_data = pd.read_excel(excel_file_path)
    excel_data = excel_data[excel_data.count(axis=1) > 1]
    excel_data.to_excel(excel_file_path, index=False)

def auto_fit_columns(excel_file_path):
    wb = load_workbook(excel_file_path)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        header_fill = PatternFill(start_color="D4AC0D", end_color="D4AC0D", fill_type="solid")  # Gray color
        header_font = Font(bold=True)

        for col_idx, column_cells in enumerate(ws.columns, start=1):
            max_length = max(len(str(cell.value)) for cell in column_cells)
            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = adjusted_width

            for cell in column_cells:
                if cell.row == 1:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.value = str(cell.value).upper()
                    
    wb.save(excel_file_path)

def highlight_n_check_prediction(excel_file_path):

    def compare_address(str1, address, threshold=60):
        similarity_ratio = fuzz.token_set_ratio(clean_string(str(str1)).lower(), clean_string(str(address)).lower())
        new_ratio = similarity_ratio <= threshold
        
        if new_ratio:
            check = str1.replace(' ', '').replace('Ñ', 'N').lower() not in address.replace(' ', '').replace('Ñ', 'N').lower()
            if not check:
                new_ratio = check

        return new_ratio
    
    df = pd.read_excel(excel_file_path)
    area_index = df.columns.get_loc('AREA') + 1
    municipality_index = df.columns.get_loc('MUNICIPALITY') + 1
    final_area_index = df.columns.get_loc('FINAL AREA') + 1
    autofield_date_index = df.columns.get_loc('AUTOFIELD DATE') + 1
    
    book = load_workbook(excel_file_path)
    sheet = book.active

    for row_index, row in df.iterrows():
        address = str(row['ADDRESS']).lower()

        cell1 = sheet.cell(row=row_index + 2, column=area_index)
        cell2 = sheet.cell(row=row_index + 2, column=municipality_index)
        cell3 = sheet.cell(row=row_index + 2, column=final_area_index)
        cell4 = sheet.cell(row=row_index + 2, column=autofield_date_index)

        if not address.strip():
            cell1.value = cell2.value = ''
        else:
            cell3.value = cell4.value = ''

            area = str(row["AREA"]).lower()
            municipality = str(row["MUNICIPALITY"]).lower()

            if compare_address(area, address) and compare_address(municipality, address):
                cell1.fill = cell2.fill = PatternFill(start_color="ffa500", end_color="ffa500", fill_type="solid")
            elif compare_address(area, address):
                cell1.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")
            elif compare_address(municipality, address):
                cell2.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")
            else:
                cell3.value = row["AREA"]

    book.save(excel_file_path)

def delete_requests_file(folder_path):
    files_to_delete = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        os.remove(file_path)