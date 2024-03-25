import os
import pandas as pd
from pandas import ExcelWriter
from flask import Flask, render_template, request, jsonify, send_file
from flask_uploads import UploadSet, configure_uploads, DATA
from werkzeug.utils import secure_filename
import random
from datetime import datetime
from flask_socketio import SocketIO
from time import sleep, time
import functions as func
import joblib
from predict import load_model_predict
from train import train_model_save_joblib
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

directory_path = os.path.join(os.path.expanduser("~"), "Desktop")

app.config['UPLOADED_FILES_DEST'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['SOURCE_FILES_DEST'] = os.getenv('SOURCE_FOLDER', 'source')
files = UploadSet('files', DATA)
configure_uploads(app, files)

@app.route('/download_file')
def download_file():
    # Path to the file you want to download
    file_path = './source/template.xlsx'

    # Return the file as an attachment
    return send_file(file_path, as_attachment=True)

@app.route('/feed', methods=['POST'])
def feed():
    status = False
    
    try:
        file = request.files.get('file')  # Safely get file

        if not file:
            return jsonify({"message": "No file uploaded", "status": status}), 400
        
        file_name = secure_filename(file.filename)

        if not os.path.exists(app.config['UPLOADED_FILES_DEST']):
            os.makedirs(app.config['UPLOADED_FILES_DEST'])

        file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], file_name)

        file.save(file_path)

        df1 = pd.read_excel(file_path)

        model_path = os.path.join(app.config['SOURCE_FILES_DEST'], "model.xlsx")
        df2 = pd.read_excel(model_path)

        if list(df1.columns) == list(df2.columns):
            combined_df = pd.concat([df2, df1], ignore_index=True)
            combined_df.to_excel(model_path, index=False)

            train_model_save_joblib(model_path)

            status = True

            return jsonify({"message": "New data has been fed", "status": status})

    except FileNotFoundError:
        return jsonify({"message": "File not found", "status": status}), 404
    except pd.errors.ParserError:
        return jsonify({"message": "Error parsing Excel file", "status": status}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}", "status": status}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)  # Clean up the uploaded file


@app.route('/predict', methods=['POST'])
def upload():
    file = request.files['file']
    file_name = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], file_name)
    file.save(file_path)

    try:
        result_path = load_model_predict(file_path)
        
        return send_file(result_path, as_attachment=True)
    finally:
        os.remove(file_path)  # Clean up the uploaded file

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
    output_file_path = None
    
    try:
        status = False
        
        if not os.path.exists(directory_path):
            message = f"The system cannot find the path specified: {directory_path}"
            data_to_return = {'message': message, 'status': status}
            return jsonify(data_to_return)
        
        bank_name = request.form['bank_name']
        
        merge_excel_folder = os.path.join(directory_path, "Merge-Excel")
        
        if not os.path.exists(merge_excel_folder):
            os.makedirs(merge_excel_folder)
        
        folder_path = os.path.join(directory_path, "Requests", bank_name)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.xlsx')]
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if not files:
            message = f"No existing file inside {bank_name}"
            data_to_return = {'message': message, 'status': status}
            return jsonify(data_to_return)

        template_path = os.path.join(app.config['SOURCE_FILES_DEST'], "template.xlsx")
        
        template_header = pd.read_excel(template_path).columns.to_list()
        
        mapping = {
            "ADDRESS TYPE": "ADD TYPE",
            "ADD": "ADDRESS",
            "REQUEST DATE": "DATE REQUESTED",
            "REQUEST NAME": "REQUESTED BY",
            "DATE": "DATE REQUESTED"
            # Add more mappings as needed
        }

        total_files = len(files)
        work_progress = total_files + 6
        
        def set_progress(progress):
            socketio.emit("update progress", progress)
            sleep(1)

        main_df = pd.DataFrame()
        additional_header = set()
        
        set_progress(0)
        
        for i, file in enumerate(files):         
            excel_file_path = os.path.join(folder_path, file)
            index_header = func.get_index_of_header(excel_file_path, template_header)
            sheet_data = pd.read_excel(excel_file_path, sheet_name=0, header=index_header)
            
            sheet_columns = sheet_data.columns.to_list()
            
            temp_df = pd.DataFrame()
            encoded_columns = set()
            
            for header in template_header:
                isIn = False

                for col_header in sheet_columns:
                    if header == func.map_header(mapping, col_header):
                        temp_df[func.map_header(mapping, col_header)] = sheet_data[col_header].astype(str)
                        encoded_columns.add(col_header)
                        isIn = True
                        break

                    elif func.compare_string(header, col_header):
                        temp_df[header] = sheet_data[col_header].astype(str)
                        encoded_columns.add(col_header)
                        isIn = True
                        break

                if not isIn:
                    temp_df[header] = ''
            
            not_encoded_columns = [x for x in sheet_columns if x not in encoded_columns]
            
            for col_header in not_encoded_columns:
                isIn = False
                
                for header in additional_header:
                    if func.compare_string(header, col_header):
                        temp_df[header] = sheet_data[col_header].astype(str)
                        isIn = True
                        break
                    
                if not isIn and "UNNAMED" not in func.clean_string(col_header) and not func.is_empty_or_spaces(col_header):
                    temp_df[func.clean_string(col_header).strip()] = sheet_data[col_header].astype(str)
                    additional_header.add(func.clean_string(col_header))
                    
            main_df = pd.concat([main_df, temp_df], ignore_index=True)

            set_progress((i + 1) / work_progress * 100)
            
        current_date = datetime.now().strftime("%Y-%m-%d")
        output_file_name = f"Output-{bank_name}-{current_date}-{int(time())}.xlsx"
        output_file_path = os.path.join(merge_excel_folder, output_file_name)
        
        main_df['ADDRESS'] = main_df['ADDRESS'].str.upper()
        main_df.to_excel(output_file_path, index=False)
        
        set_progress((total_files + 1) / work_progress * 100)

        model = joblib.load('source\\model.joblib')
        output_work_book = pd.read_excel(output_file_path)

        set_progress((total_files + 2) / work_progress * 100)
        
        existing_mask = (output_work_book['AREA'].notna()) & (output_work_book['MUNICIPALITY'].notna())
        
        addresses = output_work_book.loc[~existing_mask, 'ADDRESS'].tolist()
        addresses = output_work_book.loc[~existing_mask & output_work_book['ADDRESS'].notna(), 'ADDRESS'].tolist()
        
        prediction_mask = output_work_book['ADDRESS'].isin(addresses)
        print(f'Number of addresses to predict: {len(addresses)}')  # Debugging line

        set_progress((total_files + 3) / work_progress * 100)
        
        if addresses:
            predictions = model.predict(addresses) 
        else:
            predictions = []

        print(f'Number of predictions: {len(predictions)}')  # Debugging line
        
        area_munis = [prediction.split('-') for prediction in predictions]
        
        output_work_book.loc[prediction_mask, 'AREA'] = [area_muni[0] for area_muni in area_munis]
        output_work_book.loc[prediction_mask, 'MUNICIPALITY'] = [area_muni[1] for area_muni in area_munis]
        
        output_work_book.to_excel(output_file_path, index=False)

        set_progress((total_files + 4) / work_progress * 100)
        
        func.drop_row_with_one_cell(output_file_path)
        func.highlight_n_fill_missing_values(output_file_path, 'source\\campaign_list.json' )

        set_progress((total_files + 5) / work_progress * 100)

        func.highlight_n_check_prediction(output_file_path)
        func.auto_fit_columns(output_file_path)

        set_progress((total_files + 6) / work_progress * 100)

        message = f"Excel file created successfully for {bank_name}. Output file: <strong><a href='file:///{output_file_path}' target='_blank'>{output_file_name}</a></strong>."
        status = True

    except Exception as e:
        message = f"{e}"
        
        if output_file_path:
            os.remove(output_file_path)
        
    data_to_return = {'message': message, 'file_path': folder_path, 'status': status}

    sleep(1)

    return jsonify(data_to_return)
@app.route('/sleep')
def sleep_computer():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Computer is going to sleep!"
    
@app.route('/', methods=['GET'])
def index():
    requests_folder = os.path.join(directory_path, "Requests")

    message = "None"
    status = False

    if not os.path.exists(requests_folder):
        os.makedirs(requests_folder)
    
    # Get bank names using folder
    bank_names = [folder.upper() for folder in os.listdir(requests_folder) if os.path.isdir(os.path.join(requests_folder, folder))]

    escaped_requests_folder = requests_folder.replace('\\', '\\\\')

    if not bank_names:
        message = f"Please create folder for campaigns in <strong><span id='folderName'>{escaped_requests_folder}</span><i class='fa fa-copy copy-icon' style='cursor:pointer;margin-left:5px;' onclick='copyToClipboard(\"{escaped_requests_folder}\")'></i></strong></span>"
        status = True
        

    # JavaScript function to copy the folder name to clipboard
    javascript_function = """
    <script>
  function copyToClipboard(text) {
    var tempInput = document.createElement("input");
    tempInput.value = text;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);
    
    Swal.fire({
        title: "Paste In file manager:",
        text: text,
        showCancelButton: false,
        confirmButtonColor: "#3085d6",
        confirmButtonText: "OK"
    });
}
    </script>
    """

    complete_message = message + javascript_function

    return render_template('index.html', bank_names=bank_names, no_error=status, message=complete_message)

# with app.app_context():
#     # Create the database tables
#     db.create_all()

if __name__ == '__main__':
    socketio.run(app=app, debug=True, host="0.0.0.0", port=8000)
