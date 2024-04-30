from fuzzywuzzy import fuzz  # Importing fuzzywuzzy library for string matching
import json  # Importing json module to work with JSON data
import re  # Importing re module for regular expressions
from openpyxl.styles import PatternFill, Font  # Importing necessary styles from openpyxl
from openpyxl import load_workbook  # Importing load_workbook function from openpyxl
import pandas as pd  # Importing pandas library for data manipulation
import os  # Importing os module for interacting with the operating system


def get_total_rows(file_path) -> int:
    """
    Get total number of rows in an Excel file.

    Parameters:
    file_path (str): Path to the Excel file.

    Returns:
    int: Total number of rows.
    """
    workbook = load_workbook(file_path)
    worksheet = workbook.active
    return worksheet.max_row


def clean_string(input_string):
    """
    Clean and normalize a string.

    Parameters:
    input_string (str): Input string to be cleaned.

    Returns:
    str: Cleaned and normalized string.
    """
    return re.sub(r'[^a-zA-Z0-9\s]', ' ', input_string).upper()


def is_empty_or_spaces(s):
    """
    Check if a string is empty or contains only spaces.

    Parameters:
    s (str): Input string.

    Returns:
    bool: True if the string is empty or contains only spaces, False otherwise.
    """
    return s.replace(' ', '') == ''


def compare_string(str1, str2, threshold=90):
    """
    Compare two strings for similarity using fuzzy string matching.

    Parameters:
    str1 (str): First string.
    str2 (str): Second string.
    threshold (int): Minimum similarity threshold (default is 90).

    Returns:
    bool: True if the strings are similar, False otherwise.
    """
    similarity_ratio = fuzz.token_set_ratio(clean_string(str(str1)).lower(), clean_string(str(str2)).lower())
    return similarity_ratio >= threshold


def check_sub(string1, string2):
    """
    Check if both strings contain 'SUB' or neither contains 'SUB'.

    Parameters:
    string1 (str): First string.
    string2 (str): Second string.

    Returns:
    bool: True if both strings contain 'SUB' or neither contains 'SUB', False otherwise.
    """
    return ("SUB" in string1 and "SUB" in string2) or ("SUB" not in string1 and "SUB" not in string2)


def find_header(row_values, template_header):
    """
    Find if any header matches in the row values.

    Parameters:
    row_values (list): List of row values.
    template_header (list): List of template headers to match.

    Returns:
    bool: True if any header matches, False otherwise.
    """
    for data in row_values:
        for header in template_header:
            if compare_string(data, header):
                return True
    return False


def get_index_of_header(excel_file_path, template_header) -> int:
    """
    Get the index of the row containing the header in the Excel file.

    Parameters:
    excel_file_path (str): Path to the Excel file.
    template_header (list): List of template headers to match.

    Returns:
    int: Index of the row containing the header, -1 if not found.
    """
    sheet_data = pd.read_excel(excel_file_path, sheet_name=0, header=None)
    if sheet_data.empty:
        return -1
    for index, row in sheet_data.iterrows():
        if find_header(row.values, template_header):
            return index
    return -1


def map_header(mapping, header):
    """
    Map header to a predefined mapping.

    Parameters:
    mapping (dict): Dictionary mapping headers.
    header (str): Header to map.

    Returns:
    str: Mapped header, or None if not found.
    """
    cleaned_header = clean_string(header)
    return mapping.get(cleaned_header, None)


def highlight_n_fill_missing_values(excel_file_path, campaign_file_path):
    """
    Highlight and fill missing values in the Excel file based on a campaign data file.

    Parameters:
    excel_file_path (str): Path to the Excel file.
    campaign_file_path (str): Path to the campaign data JSON file.
    """
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
    """
    Drop rows from the Excel file where there is only one cell containing data.

    Parameters:
    excel_file_path (str): Path to the Excel file.
    """
    excel_data = pd.read_excel(excel_file_path)
    excel_data = excel_data[excel_data.count(axis=1) > 1]   
    excel_data.to_excel(excel_file_path, index=False)


def auto_fit_columns(excel_file_path):
    """
    Automatically adjust column widths and format headers in the Excel file.

    Parameters:
    excel_file_path (str): Path to the Excel file.
    """
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
    """
    Clean and normalize an address.

    Parameters:
    address (str): Input address string.

    Returns:
    str: Cleaned and normalized address string.
    """
    address = re.sub(r"[^a-zA-Z0-9\s]", " ", re.sub(r"[^\w\s`~!@#$%^&*()\_\-+=\[\]{};:'\"\\|,<.>\/]", "N", address.upper().replace('Ñ', 'N'))).split()

    abbreviation = {
        "GEN": "GENERAL",
        "STA": "SANTA",
        "STO": "SANTO",
        "NATIONAL CAPITAL REGION": "NCR",
        "METRO MANILA": "NCR"
    }
    
    for key, value in abbreviation.items():
        address = [value if word == key else word for word in address]

    address = ' '.join(list(filter(lambda item: item.strip(), address)))

    area = {
        "NATIONAL CAPITAL REGION": "NCR",
        "METRO MANILA": "NCR",
        "AUTONOMOUS REGION IN MUSLIM MINDANAO": "ARMM",
        "BANGSAMORO AUTONOMOUS REGION IN MUSLIM MINDANAO": "BARMM",
        "CORDILLERA ADMINISTRATIVE REGION": "CAR",
        "SOCSARGEN": "SOCCSKSARGEN",
        "CITY": " CITY "        
    }
        
    for key, value in area.items():
        address = address.replace(key, value) if key in address else address
        
    return ' '.join(list(filter(lambda item: item.strip(), address.split())))


def remove_numbers(address):
    """
    Remove numbers from an address.

    Parameters:
    address (str): Input address string.

    Returns:
    str: Address string with numbers removed.
    """
    return clean_address(re.sub(r"\d+", "", address).upper())


def clean_province(province):
    """
    Clean and normalize a province name.

    Parameters:
    province (str): Input province name.

    Returns:
    str: Cleaned and normalized province name.
    """
    suffix = ["DEL", "NORTE", "SUR", "DE ORO", "OCCIDENTAL", "ORIENTAL", "EASTERN", "NORTHERN", "SOUTHERN", "WESTERN", "NORTH", "SOUTH", "ISLAND"]
        
    province_parts = province.split()
        
    cleaned_province_parts = [part.strip() for part in province_parts if part.upper() not in suffix]
        
    cleaned_province = " ".join(cleaned_province_parts)
        
    return cleaned_province


def compare_address(str1, address, threshold=60):
    """
    Compare a string with an address for similarity.

    Parameters:
    str1 (str): First string to compare.
    address (str): Address string to compare.
    threshold (int): Minimum similarity threshold (default is 60).

    Returns:
    bool: True if the strings are similar, False otherwise.
    """
    if str1.replace(' ', '').replace('Ñ', 'N') in address.replace(' ', '').replace('ñ', 'n').replace('Ñ', 'N'):
        return False

    return True

def check_city(area, municipality):
    if area not in municipality and "CITY" in municipality and "QUEZON" not in municipality:
        return municipality.replace("CITY", "").strip()
    return municipality


def highlight_n_check_prediction(excel_file_path):    
    """
    Highlight and check prediction accuracy for addresses in the Excel file.

    Parameters:
    excel_file_path (str): Path to the Excel file.
    """
    df = pd.read_excel(excel_file_path)

    area_index = df.columns.get_loc('AREA') + 1
    municipality_index = df.columns.get_loc('MUNICIPALITY') + 1
    final_area_index = df.columns.get_loc('FINAL AREA') + 1
    autofield_date_index = df.columns.get_loc('AUTOFIELD DATE') + 1
    
    book = load_workbook(excel_file_path)
    sheet = book.active

    pattern_fill = PatternFill(start_color="ffa500", end_color="ffa500", fill_type="solid")

    for row_index, row in df.iterrows():
        address = remove_numbers(str(row['ADDRESS']))

        cell1 = sheet.cell(row=row_index + 2, column=area_index)
        cell2 = sheet.cell(row=row_index + 2, column=municipality_index)
        cell3 = sheet.cell(row=row_index + 2, column=final_area_index)
        cell4 = sheet.cell(row=row_index + 2, column=autofield_date_index)

        cell3.value = cell4.value = ''

        area = str(row["AREA"])
        municipality = str(row["MUNICIPALITY"])

        if '**' in area and '**' in municipality:
            cell1.font = cell2.font = Font(bold=True)
            cell1.value = area = area.replace('**', '')
            cell2.value = municipality = municipality.replace('**', '')

        if (compare_address(clean_province(area), address) and compare_address(check_city(area, municipality), address)):
            cell1.fill = cell2.fill = PatternFill(start_color="ffa200", end_color="ffa200", fill_type="solid")

            if not address or len(address) <= 25:
                # cell1.value = cell2.value = ''
                cell1.fill = cell2.fill = PatternFill(start_color="ff4400", end_color="ff4400", fill_type="solid")

        elif compare_address(clean_province(area), address):
            cell1.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")
        elif compare_address(check_city(area, municipality), address):
           cell2.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")
            

    book.save(excel_file_path)


def delete_requests_file(folder_path):
    """
    Delete files in the specified folder.

    Parameters:
    folder_path (str): Path to the folder containing files to be deleted.
    """
    files_to_delete = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        os.remove(file_path)

if __name__ == "__main__":
    print(compare_string("Disposition", "sub_disposition"))
