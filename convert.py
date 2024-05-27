import json

# Path to the input JSON file containing campaign data
json_file_path = 'campaign.json'

# Open the JSON file for reading
with open(json_file_path, 'r', encoding='utf-8-sig') as json_file:
    # Load the JSON data into a Python dictionary
    data = json.load(json_file)

# Create an empty dictionary to store processed data
result_dict = {}

# Iterate over each entry in the JSON data
for value in data:
    # Extract relevant information from each entry
    code = value["CODE"]
    bank = value["BANK"]
    placement = value["PLACEMENT"]
    
    # Store the extracted information in the result dictionary
    result_dict[code] = {"BANK": bank, "PLACEMENT": placement}

# Convert the result dictionary to a JSON-formatted string with indentation
result_json = json.dumps(result_dict, indent=4)

# Path to the output JSON file where the processed data will be saved
json_file_path = 'my_list.json'

# Save the processed data (JSON-formatted string) to the output JSON file
with open(json_file_path, 'w') as json_file:
    json_file.write(result_json)
