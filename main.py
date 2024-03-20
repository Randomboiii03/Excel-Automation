import os
import pandas as pd
from pandas import ExcelWriter
from flask import Flask, render_template, request, jsonify, send_file
from flask_uploads import UploadSet, configure_uploads, DATA
from werkzeug.utils import secure_filename
import random
from datetime import datetime
from flask_socketio import SocketIO
from time import sleep
import functions as func
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from predict import load_model_predict
from train import train_model_save_joblib
import xlsxwriter
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

directory_path = os.path.join(os.path.expanduser("~"), "Desktop")

app.config['UPLOADED_FILES_DEST'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['SOURCE_FILES_DEST'] = os.getenv('SOURCE_FOLDER', 'source')
files = UploadSet('files', DATA)
configure_uploads(app, files)

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

        template_header = func.get_template_header(template_path)
        datas = [template_header]

        mapping = {
            "REQUEST DATE": "DATE REQUESTED",
            "REQUEST NAME": "REQUESTED BY",
            "ADDRESS TYPE": "ADD TYPE"
            # Add more mappings as needed
        }

        existing_headers = set()

        total_files = len(files)
        work_progress = total_files + 6
        work_progress = total_files + 6

        def set_progress(progress):
            sleep(0.75)
            sleep(0.75)
            socketio.emit("update progress", progress)
        
        set_progress(0)

        # main.py
        for i, file in enumerate(files):
            excel_file_path = os.path.join(folder_path, file)
            index_header = func.get_index_of_header(excel_file_path, template_header)
            sheet_data = pd.read_excel(excel_file_path, sheet_name=0, header=index_header)
            
            for _, row in sheet_data.iterrows():
                    output_row = []

                    # Fill out necessary column from template
                    for header in template_header:
                        value = None
                        for col_header, col_value in row.items():
                            if func.compare_string(header, col_header):
                                value = col_value
                                existing_headers.add(header)
                                break
                        output_row.append(value)

                    datas.append(output_row)

                    # Append other columns from the data frame
                    for col_header in row.keys():
                        mapped_header = func.map_header(col_header, mapping)

                        # print(mapped_header, '-', mapped_header.lower() not in [h.replace('_', '').lower() for h in template_header], mapped_header not in existing_headers, not (col_header.strip() == "" or col_header.startswith("Unnamed")), func.compare_string(mapped_header, col_header))

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
        output_file_path = os.path.join(merge_excel_folder, output_file_name)
        
        set_progress((total_files + 1) / work_progress * 100)
        
        # Make addresses in 'ADDRESS' column uppercase
        # Make addresses in 'ADDRESS' column uppercase
        output_work_book['ADDRESS'] = output_work_book['ADDRESS'].str.upper()
        output_work_book.to_excel(output_file_path, index=False)

        # Clean and fill bank and placement if missing
        campaign_file_path = 'source\\campaign_list.json' 
        func.drop_row_with_one_cell(output_file_path)
        func.highlight_n_fill_missing_values(output_file_path, campaign_file_path)

        set_progress((total_files + 2) / work_progress * 100)
        print('LOADING MODEL')
        model = joblib.load('source\\model.joblib')
        output_work_book = pd.read_excel(output_file_path)

        set_progress((total_files + 3) / work_progress * 100)
        print('PREDICTING')
        # Define a mask for rows where 'AREA' and 'MUNICIPALITY' already have values
        existing_mask = (output_work_book['AREA'].notna()) & (output_work_book['MUNICIPALITY'].notna())
        # Extract non-empty addresses from the 'ADDRESS' column
        addresses = output_work_book.loc[~existing_mask, 'ADDRESS'].tolist()
        addresses = output_work_book.loc[~existing_mask & output_work_book['ADDRESS'].notna(), 'ADDRESS'].tolist()
        # Create a new mask for rows that were used for prediction
        prediction_mask = output_work_book['ADDRESS'].isin(addresses)
        print(f'Number of addresses to predict: {len(addresses)}')  # Debugging line

        # Make predictions using the model
        if addresses:
            predictions = model.predict(addresses) 
        else:
            predictions = []

        print(f'Number of predictions: {len(predictions)}')  # Debugging line

        print('SPLITTING')
        # Split predictions into AREA and MUNICIPALITY
        area_munis = [prediction.split('-') for prediction in predictions]

        # Update the DataFrame with predictions only for the rows that were used for prediction
        output_work_book.loc[prediction_mask, 'AREA'] = [area_muni[0] for area_muni in area_munis]
        output_work_book.loc[prediction_mask, 'MUNICIPALITY'] = [area_muni[1] for area_muni in area_munis]

        # Save the updated DataFrame to the same Excel file
        output_work_book.to_excel(output_file_path, index=False)

        set_progress((total_files + 4) / work_progress * 100)

        func.highlight_n_check_prediction(output_file_path)
        func.auto_fit_columns(output_file_path)

        set_progress((total_files + 5) / work_progress * 100)

        func.highlight_n_check_prediction(output_file_path)
        func.auto_fit_columns(output_file_path)

        set_progress((total_files + 6) / work_progress * 100)

        message = f"Excel file created successfully for {bank_name}. Output file: <strong><a href='file:///{output_file_path}' target='_blank'>{output_file_name}</a></strong>."
        status = True

    except Exception as e:
        message = f"{e}"
        # Check if output_file_path is not None before trying to remove it
        if output_file_path is not None:
            os.remove(output_file_path)
        

    data_to_return = {'message': message, 'file_path': folder_path, 'status': status}

    sleep(1)

    return jsonify(data_to_return)


@app.route('/download_file')
def download_file():
    # Path to the file you want to download
    file_path = './source/template.xlsx'

    # Return the file as an attachment
    return send_file(file_path, as_attachment=True)

@app.route('/feed', methods=['POST'])
def feed():
    status = False
    
    file = request.files.get('file')  # Safely get file
    if file:
        try:
            file_name = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], file_name)
            file.save(file_path)

            df1 = pd.read_excel(file_path)

            model_path = os.path.join(app.config['SOURCE_FILES_DEST'], "model.xlsx")
            df2 = pd.read_excel(model_path)

            if list(df1.columns) == list(df2.columns):
                combined_df = pd.concat([df2, df1], ignore_index=True)
                combined_df.to_excel(model_path, index=False)

                train_model_save_joblib()

                status = True
                return jsonify({"message": "New data has been fed", "status": status})
            else:
                return jsonify({"message": "Wrong column format", "status": status})
        except FileNotFoundError:
            return jsonify({"message": "File not found", "status": status}), 404
        except pd.errors.ParserError:
            return jsonify({"message": "Error parsing Excel file", "status": status}), 400
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}", "status": status}), 500
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up the uploaded file
    else:
        return jsonify({"message": "No file uploaded", "status": status}), 400

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

if __name__ == '__main__':
    socketio.run(app=app, debug=True, host="0.0.0.0", port=8000)
