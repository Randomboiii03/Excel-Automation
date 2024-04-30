import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from flask_uploads import UploadSet, configure_uploads, DATA
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from predict import Predict
from train import train_model_save_joblib
from database import DB as db
import functions as func
from dotenv import load_dotenv
from datetime import datetime
from time import sleep, time
import shutil

load_dotenv()

class MyApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.app.config['UPLOADED_FILES_DEST'] = os.getenv('UPLOAD_FOLDER', 'uploads')
        self.app.config['SOURCE_FILES_DEST'] = os.getenv('SOURCE_FOLDER', 'source')

        # Ensure the uploads folder exists
        os.makedirs(self.app.config['UPLOADED_FILES_DEST'], exist_ok=True)

        self.files = UploadSet('files', DATA)
        configure_uploads(self.app, self.files)
        self.directory_path = os.path.join(os.path.expanduser("~"), "Desktop")

        self.app.add_url_rule('/download_file', 'download_file', self.download_file)
        self.app.add_url_rule('/feed', 'feed', self.feed, methods=['POST'])
        self.app.add_url_rule('/predict', 'predict', self.predict, methods=['POST'])
        self.app.add_url_rule('/delete', 'delete', self.delete, methods=['POST'])
        self.app.add_url_rule('/merge', 'merge', self.merge, methods=['POST'])
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])


    def __del__(self):
        self.socketio.stop()


    def download_file(self):
        file_path = os.path.join(self.app.config['SOURCE_FILES_DEST'], 'data_feed_template.xlsx')
        return send_file(file_path, as_attachment=True)


    def feed(self):
        try:
            # Create database if not exists
            db().create()

            # Get the uploaded file
            file = request.files.get('file')
            if not file:
                return jsonify({"message": "No file uploaded", "status": False}), 400

            # Securely save the file
            file_name = secure_filename(file.filename)
            file_path = os.path.join(self.app.config['UPLOADED_FILES_DEST'], file_name)
            file.save(file_path)

            # Read the uploaded Excel file
            df = pd.read_excel(file_path)

            # Check if the required columns are present
            required_columns = ['area-muni', 'address']
            if not all(col in df.columns for col in required_columns):
                return jsonify({"message": "Uploaded file has the wrong column format, make sure headers are in lower", "status": False}), 404

            # Insert data into the database
            inserted_data = db().insert(df.drop_duplicates())
            if inserted_data < 0:
                return jsonify({"message": "Something went wrong with database", "status": False}), 404
            elif inserted_data == 0:
                return jsonify({"message": "All data is already fed", "status": True}), 200

            # Train and save the model
            if not train_model_save_joblib():
                return jsonify({"message": "Something went creating a new model", "status": False}), 404

            return jsonify({"message": "New data has been fed", "status": True})

        except FileNotFoundError:
            return jsonify({"message": "File not found", "status": False}), 404
        except pd.errors.ParserError:
            return jsonify({"message": "Error parsing Excel file", "status": False}), 400
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}", "status": False}), 500
        finally:
            # Clean up the uploaded file
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)


    def predict(self):
        try:
            file = request.files.get('file')
            if not file:
                return jsonify({"message": "No file uploaded", "status": False}), 400

            file_name = secure_filename(file.filename)
            file_path = os.path.join(self.app.config['UPLOADED_FILES_DEST'], file_name)
            file.save(file_path)

            print(file_path)
            model_path = os.path.join(self.app.config['SOURCE_FILES_DEST'], "model.joblib")
            # result_path = os.path.join(self.app.config['UPLOADED_FILES_DEST'], "predictions.xlsx")

            if not os.path.exists(model_path):
                return 'No model yet', 500

            predict = Predict()
            result_path = predict.geocode_only(file_path)
            print(result_path)

            return send_file(result_path, as_attachment=True), 200
        
        except FileNotFoundError:
            return jsonify('File not found'), 404
        except pd.errors.ParserError:
            return jsonify('Error parsing Excel file'), 400
        except Exception as e:
            print(f'Error: {e}')
            return f'Error: {e}', 500
        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)


    def delete(self):
        try:
            data = request.json
            folder_path = data.get('data')

            func.delete_requests_file(folder_path)

            bank_name = os.path.basename(folder_path)

            return jsonify({'message': f"Deleted all files in folder: {bank_name}", 'status': True})
        except Exception as e:
            return jsonify({'message': f"Error: {e}", 'status': False})


    def merge(self):
        output_file_path = None
        
        try:
            status = False
            
            if not os.path.exists(self.directory_path):
                return jsonify({'message': f"The system cannot find the path specified: {self.directory_path}", 'status': status})
            
            bank_name = request.form['bank_name']
            
            merge_excel_folder = os.path.join(self.directory_path, "Merge-Excel")
            os.makedirs(merge_excel_folder, exist_ok=True)
            
            folder_path = os.path.join(self.directory_path, "Requests", bank_name)
            os.makedirs(folder_path, exist_ok=True)
            
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.xlsx')]
            
            if not files:
                return jsonify({'message': f"No existing file inside {bank_name}", 'status': status})

            template_path = os.path.join(self.app.config['SOURCE_FILES_DEST'], "template.xlsx")
            
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
            work_progress = total_files + 5
            
            def set_progress(progress):
                self.socketio.emit("update progress", progress)
                sleep(1)

            main_df = pd.DataFrame()
            additional_header = set()
            
            set_progress(0)
            
            for i, file in enumerate(files):         
                excel_file_path = os.path.join(folder_path, file)
                index_header = func.get_index_of_header(excel_file_path, template_header)

                if index_header == -1:
                    return jsonify({'message': f"Can't find header: {file}", 'status': status})

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
                        if func.compare_string(header, col_header) and func.check_sub(func.clean_string(col_header), header):
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

            main_df.to_excel(output_file_path, index=False)

            predict = Predict().merge_it(output_file_path)
            set_progress((total_files + 1) / work_progress * 100)
            
            func.drop_row_with_one_cell(output_file_path)
            set_progress((total_files + 2) / work_progress * 100)

            func.highlight_n_fill_missing_values(output_file_path, os.path.join(self.app.config['SOURCE_FILES_DEST'], 'campaign_list.json'))
            set_progress((total_files + 3) / work_progress * 100)

            func.highlight_n_check_prediction(output_file_path)
            set_progress((total_files + 4) / work_progress * 100)
            
            func.auto_fit_columns(output_file_path)
            set_progress((total_files + 5) / work_progress * 100)

            # if os.path.exists(output_file_path):
            #     shutil.copy(output_file_path, output_file_path.replace('INCOMPLETE-', ''))

            message = f"Excel file created successfully for {bank_name}. Output file: <strong>{output_file_path}</strong>."
            status = True

        except Exception as e:
            message = f"{e}"
            try:
                if 'output_file_path' in locals() and os.path.exists(output_file_path):
                    os.remove(output_file_path)

            except OSError as e:
                print(f"Error deleting file: {e}")
            

            
        data_to_return = {'message': message, 'file_path': folder_path, 'status': status}

        return jsonify(data_to_return)

    
    def index(self):
        requests_folder = os.path.join(self.directory_path, "Requests")
        bank_names = []

        if not os.path.exists(requests_folder):
            os.makedirs(requests_folder)

        for folder in os.listdir(requests_folder):
            if os.path.isdir(os.path.join(requests_folder, folder)):
                bank_names.append(folder.upper())

        escaped_requests_folder = requests_folder.replace('\\', '\\\\')

        message = f"Please create folder for campaigns in <strong><span id='folderName'>{escaped_requests_folder}</span><i class='fa fa-copy copy-icon' style='cursor:pointer;margin-left:5px;' onclick='copyToClipboard(\"{escaped_requests_folder}\")'></i></strong></span>" if not bank_names else "None"
        status = not bank_names

        # JavaScript function to copy the folder name to clipboard
        javascript_function = """
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
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
                toast: true,
                position: 'center',
                showConfirmButton: false,
                timer: 3000
            });
        }
        </script>
        """

        complete_message = message + javascript_function

        return render_template('index.html', bank_names=bank_names, no_error=status, message=complete_message)


    def run(self):
        self.socketio.run(app=self.app, debug=True, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    my_app = MyApp()
    my_app.run()