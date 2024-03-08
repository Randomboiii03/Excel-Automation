import os
import pandas as pd
from fuzzywuzzy import fuzz, process
import openpyxl
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_template_header(file_path):
    return pd.read_excel(file_path).columns.to_list()

def compare_string(str1, str2, threshold=90):
    similarity_ratio = fuzz.token_set_ratio(str(str1).lower(), str(str2).lower())
    return similarity_ratio >= threshold

def find_header(row_values, template_header):
    row_list = row_values.tolist()

    count = sum(compare_string(data, header) for header in template_header for data in row_list)
    print(f"COUNT: {count}")
    return count >= 4

def get_index_of_header(excel_file_path, template_header) -> tuple[int, list]:
    work_book = pd.read_excel(excel_file_path, sheet_name=None, header=None)
    
    for sheet_name, sheet_data in work_book.items():
        if sheet_data.empty:
            return 0

        for index, row in sheet_data.iterrows():
            if find_header(row.values, template_header):
                return index, row.values.tolist()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        bank_name = request.form['bank_name']
        folder_path = os.path.join("C:\\Users\\SPM\\Documents\\BANK LIST", bank_name)
        
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        template_header = get_template_header("Template.xlsx")
        datas = [template_header]

        for file in files:
            excel_file_path = os.path.join(folder_path, file)

            # Find and get header's index(location/row)
            index_header, current_header = get_index_of_header(excel_file_path, template_header)

            work_book = pd.read_excel(excel_file_path, sheet_name=None, header=index_header)

            for sheet_name, sheet_data in work_book.items():
                for index, row in sheet_data.iterrows():       
                    keys, values = zip(*row.items())     

                    output_list = []

                    for header in template_header:
                        isSame = False
                        for key, value in zip(keys, values):
                            if compare_string(header, key): 
                                output_list.append(value)
                                isSame = True
                                break
                        
                        if not isSame:
                            output_list.append("")
                        
                    datas.append(output_list)

        work_book = openpyxl.Workbook()
        sheet = work_book.active

        for row_data in datas:
            sheet.append(row_data)

        # Save the workbook to a file
        output_file_name = "Output_" + bank_name + ".xlsx"
        output_file_path = os.path.join("C:\\Users\\SPM\\Documents", output_file_name)
        work_book.save(output_file_path)

        return f"Excel file created successfully for {bank_name}."

    return render_template('index.html')

if __name__ == '__main__':
    app.run()