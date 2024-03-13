import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
import random
from datetime import datetime
from flask_socketio import SocketIO
from time import sleep
import functions as func
from pathlib import Path

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/delete', methods=['POST'])
def delete():
    try:
        status = False

        data = request.json
        folder_path = data.get('data')
        
        func.delete_requests_file(folder_path)

        bank_name = folder_path.split("\\")

        message = f"Deleted all files in folder: {bank_name[-1]}"
        data_to_return = {'message': message, 'status': status}
    except Exception as e:
        message = f"{e}"
    
    data_to_return = {'message': message, 'status': status}
        
    return jsonify(data_to_return)

@app.route('/merge', methods=['POST'])
def merge():
    try:
        status = False

        directory_path = "C:\\Users\\SPM\\Desktop\\ONLY SAVE FILES HERE\\Requests"

        if not os.path.exists(directory_path):
            message = f"The system cannot find the path specified: {directory_path}"
            data_to_return = {'message': message, 'status': status}
            return jsonify(data_to_return)

        bank_name = request.form['bank_name']

        folder_path = os.path.join(directory_path, bank_name)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.xlsx')]
        
        if not files:
            message = f"No existing file inside {bank_name}"
            data_to_return = {'message': message, 'status': status}
            return jsonify(data_to_return)

        template_header = func.get_template_header("Template.xlsx")
        datas = [template_header]

        mapping = {
            "REQUEST DATE": "DATE REQUESTED",
            "REQUEST NAME": "REQUESTED BY"
            # Add more mappings as needed
        }

        existing_headers = set()

        total_files = len(files)
        work_progress = total_files + 4

        def set_progress(progress):
            socketio.emit("update progress", progress)

        set_progress(0)

        for i, file in enumerate(files):
            excel_file_path = os.path.join(folder_path, file)
            index_header = func.get_index_of_header(excel_file_path, template_header)
            work_book = pd.read_excel(excel_file_path, sheet_name=None, header=index_header)

            for _, sheet_data in work_book.items():
                for _, row in sheet_data.iterrows():
                    output_row = []

                    # Fill out necessary column from template
                    for header in template_header:
                        value = None
                        for col_header, col_value in row.items():
                            if func.compare_string(header, col_header):
                                value = col_value
                                break
                        output_row.append(value)

                    datas.append(output_row)

                    # Append other columns from the data frame
                    for col_header in row.keys():
                        mapped_header = func.map_header(col_header, mapping)

                        if mapped_header.lower() not in [h.lower() for h in template_header] and mapped_header not in existing_headers and not (col_header.strip() == "" or col_header.startswith("Unnamed")) and func.compare_string(mapped_header, col_header):
                            datas[0].append(mapped_header)
                            output_row.append(row[col_header])
                            existing_headers.add(mapped_header)
                            
            set_progress((i + 1) / work_progress * 100)

        # Create the merge excel file
        output_work_book = pd.DataFrame(datas[1:], columns=datas[0])
        random_number = "".join([str(random.randint(0, 9)) for _ in range(4)])
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        output_file_name = f"Output-{bank_name}-{current_date}-{random_number}.xlsx"
        output_file_path = os.path.join(directory_path, output_file_name)
        output_work_book.to_excel(output_file_path, index=False)

        set_progress((total_files + 1) / work_progress * 100)
        
        # Clean and fill bank and placement if missing
        campaign_file_path = 'campaign_list.json' 
        func.drop_row_with_one_cell(output_file_path)
        func.highlight_n_fill_missing_values(output_file_path, campaign_file_path)
        
        set_progress((total_files + 2) / work_progress * 100)
        
        # Compile addresses into one excel file
        address_column_name = "ADDRESS"
        output_address_file_name = f"Output-Address-{bank_name}-{current_date}-{random_number}.xlsx"
        output_address_file_path = os.path.join(directory_path, output_address_file_name)
        func.extract_address(output_file_path, address_column_name, output_address_file_path)

        set_progress((total_files + 3) / work_progress * 100)

        # Auto fit columns for better viewing
        func.auto_fit_columns(output_file_path)
        func.auto_fit_columns(output_address_file_path)

        set_progress((total_files + 4) / work_progress * 100)
        
        message = f"Excel file created successfully for {bank_name}. Output file: <strong><a href='file:///{output_file_path}' target='_blank'>{output_file_name}</a></strong>. Address file: <strong><a href='file:///{output_address_file_path}' target='_blank'>{output_address_file_name}</a></strong>"
        status = True

    except Exception as e:
        message = f"{e}"

    data_to_return = {'message': message, 'file_path': folder_path, 'status': status}

    sleep(1)

    return jsonify(data_to_return)

@app.route('/', methods=['GET'])
def index():
    directory_path = "C:\\Users\\SPM\\Desktop\\ONLY SAVE FILES HERE\\Requests"

    if not os.path.exists(directory_path):
        return render_template('index.html')   

    # Get bank names using folder
    bank_names = [folder.upper() for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]
    
    return render_template('index.html', bank_names=bank_names)

if __name__ == '__main__':
    socketio.run(app=app, debug=True, host="0.0.0.0", port=25565)