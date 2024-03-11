import json

json_file_path = 'campaign.json'

with open(json_file_path, 'r', encoding='utf-8-sig') as json_file:
    data = json.load(json_file)

result_dict = {}

for value in data:
    code = value["CODE"]
    bank = value["BANK"]
    placement = value["PLACEMENT"]
    result_dict[code] = {"BANK": bank, "PLACEMENT": placement}

result_json = json.dumps(result_dict, indent=4)

json_file_path = 'my_list.json'

# Save the dictionary as JSON
with open(json_file_path, 'w') as json_file:
    json_file.write(result_json)