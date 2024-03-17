import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
import random
from datetime import datetime
from flask_socketio import SocketIO
from time import sleep
import functions as func
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

directory_path = os.path.join(os.path.expanduser("~"), "Desktop")

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

        if not os.path.exists(directory_path):
            message = f"The system cannot find the path specified: {directory_path}"
            data_to_return = {'message': message, 'status': status}
            return jsonify(data_to_return)

        bank_name = request.form['bank_name']

        merge_excel_folder = os.path.join(directory_path, "Merge-Excel")
        area_break_folder = os.path.join(directory_path, "Area Break")

        if not os.path.exists(merge_excel_folder):
            os.makedirs(merge_excel_folder)

        if not os.path.exists(area_break_folder):
            os.makedirs(area_break_folder)

        folder_path = os.path.join(directory_path, "Requests", bank_name)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.xlsx')]

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

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

            set_progress((i + 1) / (2 * total_files) * 100)

        # Create the merge excel file
        output_work_book = pd.DataFrame(datas[1:], columns=datas[0])
        random_number = "".join([str(random.randint(0, 9)) for _ in range(4)])
        current_date = datetime.now().strftime("%Y-%m-%d")

        output_file_name = f"Output-{bank_name}-{current_date}-{random_number}.xlsx"
        output_file_path = os.path.join(merge_excel_folder, output_file_name)
        
         # Make addresses in 'ADDRESS' column uppercase
        output_work_book['ADDRESS'] = output_work_book['ADDRESS'].str.upper()
        
        output_work_book.to_excel(output_file_path, index=False)

        set_progress(50)

        # Clean and fill bank and placement if missing
        campaign_file_path = 'campaign_list.json' 
        func.drop_row_with_one_cell(output_file_path)
        func.highlight_n_fill_missing_values(output_file_path, campaign_file_path)

        set_progress(75)
        
        model = joblib.load('trained_model.joblib')
        
        # Step 1: Extract the 'ADDRESS' column from the output_work_book
        address_column_name = "ADDRESS"
        uploaded_addresses = output_work_book[address_column_name].fillna('').values

        # Step 2: Load the CountVectorizer used for training
        vectorizer = CountVectorizer()
        vectorizer = joblib.load('vectorizer.joblib')

        # Step 3: Transform the uploaded addresses using the loaded CountVectorizer
        uploaded_vectorized = vectorizer.transform(uploaded_addresses)

        # Step 4: Predict the muni-area and obtain probability estimates for the uploaded addresses
        predictions = model.predict(uploaded_vectorized)
        probabilities = model.predict_proba(uploaded_vectorized)

        # Step 5: Create the result DataFrame
        result_data = pd.DataFrame({
            'Address': uploaded_addresses,
            'AREA-MUNI': predictions,
            'PROBABILITY': [probabilities[i][np.where(model.classes_ == predictions[i])][0] for i in range(len(predictions))]
        })

        # Step 6: Split the 'AREA-MUNI' into 'AREA' and 'MUNICIPALITY'
        result_data[['AREA', 'MUNICIPALITY']] = result_data['AREA-MUNI'].str.split('-', expand=True)

        # Step 7: Insert the result DataFrame into the merged data
        merged_data = pd.read_excel(output_file_path)
        merged_data['AREA'] = result_data['AREA']
        merged_data['MUNICIPALITY'] = result_data['MUNICIPALITY']
        merged_data['PROBABILITY'] = result_data['PROBABILITY']
        merged_data.to_excel(output_file_path, index=False)
        
        # Auto fit columns for better viewing
        func.auto_fit_columns(output_file_path)

        set_progress(100)

        message = f"Excel file created successfully for {bank_name}. Output file: <strong><a href='file:///{output_file_path}' target='_blank'>{output_file_name}</a></strong>."
        status = True

    except Exception as e:
        message = f"{e}"

    data_to_return = {'message': message, 'file_path': folder_path, 'status': status}

    sleep(1)

    return jsonify(data_to_return)
@app.route('/add_data', methods=['POST'])
def add_data():
    # Load the trained model and vectorizer
    model = joblib.load('trained_model.joblib')
    vectorizer = joblib.load('vectorizer.joblib')

    # Read the uploaded file into a DataFrame
    file = request.files['file']
    input_data = pd.read_excel(file)

    # Extract the addresses and area-muni from the input data
    addresses = input_data['address'].fillna('').values
    area_muni = input_data['area-muni'].fillna('').values

    # Transform the addresses using the loaded vectorizer
    vectorized = vectorizer.transform(addresses)

    # Sample a subset of the new data to match the size of the existing data
    existing_size = model.partial_fit(vectorized[:1], area_muni[:1], classes=model.classes_).n_features_in_
    new_vectorized_sampled = vectorized[:existing_size]
    area_muni_sampled = area_muni[:existing_size]

    # Update the existing model with the new data
    model.partial_fit(new_vectorized_sampled, area_muni_sampled, classes=model.classes_)

    # Save the updated model
    joblib.dump(model, 'trained_model.joblib')

    return 'New data added to the model.'



    app.run()
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
