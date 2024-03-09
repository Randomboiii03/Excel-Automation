import os
import pandas as pd
from fuzzywuzzy import fuzz
from flask import Flask, render_template, request
import random
from datetime import datetime

app = Flask(__name__)

def get_template_header(file_path):
    return pd.read_excel(file_path).columns.to_list()

def compare_string(str1, str2, threshold=90):
    similarity_ratio = fuzz.token_set_ratio(str(str1).lower(), str(str2).lower())
    return similarity_ratio >= threshold

def find_header(row_values, template_header):
    row_list = row_values.tolist()
    for header in template_header:
        for data in row_list:
            if compare_string(data, header):
                return True
    return False

def get_index_of_header(excel_file_path, template_header) -> tuple[int, list]:
    work_book = pd.read_excel(excel_file_path, sheet_name=None, header=None)
    for sheet_name, sheet_data in work_book.items():
        if sheet_data.empty:
            return 0, []
        for index, row in sheet_data.iterrows():
            if find_header(row.values, template_header):
                return index, row.values.tolist()
    return 0, [""] * len(template_header)

def map_header(header, mapping):
    for key, value in mapping.items():
        if compare_string(header, key):
            return value
    return header

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    bank_names = []
    for dirpath, dirnames, filenames in os.walk("C:\\Users\\Shiroe\\Music\\BANK LIST"):
        bank_names.extend(dirnames)
        break  # Only the top-level directories are needed

    if request.method == 'POST':
        bank_name = request.form['bank_name']
        folder_path = os.path.join("C:\\Users\\Shiroe\\Music\\BANK LIST", bank_name)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        template_header = get_template_header("Template.xlsx")
        datas = [template_header]

        mapping = {
            "REQUEST DATE": "DATE REQUESTED",
            "REQUEST NAME": "REQUESTED BY"
            # Add more mappings as needed
        }

        existing_headers = set()

        for file in files:
            excel_file_path = os.path.join(folder_path, file)
            index_header, current_header = get_index_of_header(excel_file_path, template_header)
            work_book = pd.read_excel(excel_file_path, sheet_name=None, header=index_header)
            for sheet_name, sheet_data in work_book.items():
                for index, row in sheet_data.iterrows():
                    output_row = []
                    for header in template_header:
                        value = None
                        for col_header, col_value in row.items():
                            if compare_string(header, col_header):
                                value = col_value
                                break
                        output_row.append(value)
                    datas.append(output_row)

                    # Append missing columns from the file
                    for col_header in row.keys():
                        mapped_header = map_header(col_header, mapping)
                        if mapped_header not in template_header and mapped_header not in existing_headers and compare_string(mapped_header, col_header):
                            datas[0].append(mapped_header)
                            output_row.append(row[col_header])
                            existing_headers.add(mapped_header)

        output_work_book = pd.DataFrame(datas[1:], columns=datas[0])
        random_number = "".join([str(random.randint(0, 9)) for _ in range(4)])
        current_date = datetime.now().strftime("%Y-%m-%d")
        output_file_name = f"Output-{bank_name}-{current_date}-{random_number}.xlsx"
        output_file_path = os.path.join("C:\\Users\\Shiroe\\Music\\BANK LIST", output_file_name)
        output_work_book.to_excel(output_file_path, index=False)

        message = f"Excel file created successfully for {bank_name}. Output file: <strong>{output_file_name}</strong>"

    return render_template('index.html', message=message, bank_names=bank_names)

if __name__ == '__main__':
    app.run(debug=True)