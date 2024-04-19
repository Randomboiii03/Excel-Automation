from fuzzywuzzy import fuzz
import json
import re
from openpyxl.styles import PatternFill, Font
from openpyxl import load_workbook
import pandas as pd
import os


def get_total_rows(file_path) -> int:
    workbook = load_workbook(file_path)
    worksheet = workbook.active
    return worksheet.max_row

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
        return -1
    for index, row in sheet_data.iterrows():
        if find_header(row.values, template_header):
            return index
    return -1

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
    
    first_sheet_name = wb.sheetnames[0]
    ws = wb[first_sheet_name]

    header_fill = PatternFill(start_color="D4AC0D", end_color="D4AC0D", fill_type="solid")  # Gray color
    header_font = Font(bold=True)

    max_lengths = {}

    for col_idx, column_cells in enumerate(ws.columns, start=1):
        max_lengths[col_idx] = max(len(str(cell.value)) for cell in column_cells)

    for col_idx, max_length in max_lengths.items():
        adjusted_width = (max_length + 2) * 1.1
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = adjusted_width

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.value = str(cell.value).upper()
                    
    wb.save(excel_file_path)

def clean_address(address):
    address = re.sub(r"[^a-zA-Z0-9\s]", " ", address.upper().replace('Ñ', 'N')).replace("CITY", " CITY ").split()

    abbreviation = {
        "GEN": "GENERAL",
        "STA": "SANTA",
        "STO": "SANTO"
    }
    
    for key, value in abbreviation.items():
        address = [value if word == key else word for word in address]
        
    return ' '.join(list(filter(lambda item: item.strip(), address))).replace('METRO MANILA', 'NCR')

def remove_numbers(address):
    return clean_address(re.sub(r"\d+", "", address))

def clean_province(province):
    suffix = ["DEL", "NORTE", "SUR", "DE ORO", "OCCIDENTAL", "ORIENTAL", "EASTERN", "NORTHERN", "SOUTHERN", "WESTERN", "NORTH", "SOUTH", "ISLAND"]
        
    province_parts = province.split()
        
    cleaned_province_parts = [part.strip() for part in province_parts if part.upper() not in suffix]
        
    cleaned_province = " ".join(cleaned_province_parts)
        
    return cleaned_province

def compare_address(str1, address, threshold=60):
    if str1.replace(' ', '').replace('ñ', 'n').lower() in address.replace(' ', '').replace('ñ', 'n').lower():
        return False

    # similarity_ratio = fuzz.token_set_ratio(clean_string(str(str1)).lower(), clean_string(str(address)).lower())
    # return similarity_ratio <= threshold
    return True

def highlight_n_check_prediction(excel_file_path):    
    df = pd.read_excel(excel_file_path)

    area_index = df.columns.get_loc('AREA') + 1
    municipality_index = df.columns.get_loc('MUNICIPALITY') + 1
    final_area_index = df.columns.get_loc('FINAL AREA') + 1
    autofield_date_index = df.columns.get_loc('AUTOFIELD DATE') + 1
    
    book = load_workbook(excel_file_path)
    sheet = book.active

    pattern_fill = PatternFill(start_color="ffa500", end_color="ffa500", fill_type="solid")

    for row_index, row in df.iterrows():
        address = clean_address(str(row['ADDRESS'])).lower()

        cell1 = sheet.cell(row=row_index + 2, column=area_index)
        cell2 = sheet.cell(row=row_index + 2, column=municipality_index)
        cell3 = sheet.cell(row=row_index + 2, column=final_area_index)
        cell4 = sheet.cell(row=row_index + 2, column=autofield_date_index)

        if not address or len(address) <= 15:
            cell1.value = cell2.value = ''
            cell1.fill = cell2.fill = PatternFill(start_color="EE4B2B", end_color="EE4B2B", fill_type="solid")
        else:
            cell3.value = cell4.value = ''

            area = clean_province(str(row["AREA"]).lower())
            municipality = str(row["MUNICIPALITY"]).lower()

            bold_font = Font(bold=True)

            if '**' in area and '**' in municipality:
                cell1.font = cell2.font = bold_font
                area = area.replace('**', '')
                municipality = municipality.replace('**', '')
                cell1.value = area
                cell2.value = municipality

            if (compare_address(area, address) and compare_address(municipality, address)):
                cell1.fill = cell2.fill = PatternFill(start_color="ffa500", end_color="ffa500", fill_type="solid")
            elif compare_address(area, address):
                cell1.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")
            elif compare_address(municipality, address):
                cell2.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")

    book.save(excel_file_path)

def delete_requests_file(folder_path):
    files_to_delete = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        os.remove(file_path)