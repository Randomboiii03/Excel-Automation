import pandas as pd
# from openpyxl.styles import PatternFill, Font
# from openpyxl import load_workbook
# from fuzzywuzzy import fuzz

# def highlight_n_check_prediction(excel_file_path):

#     def compare_address(str1, address, threshold=60):
#         similarity_ratio = fuzz.token_set_ratio(str(str1).lower(), str(address).lower())

#         new_ratio = similarity_ratio <= threshold
#         if new_ratio:
#             check = str1.replace(' ', '').replace('Ñ', 'N').lower() not in address.replace(' ', '').replace('Ñ', 'N').lower()
#             if not check:
#                 new_ratio = check

#         return new_ratio

#     df = pd.read_excel(excel_file_path)

#     # Load the workbook
#     book = load_workbook(excel_file_path)

#     # Access the active sheet
#     sheet = book.active

#     for row_index, row in df.iterrows():
#         column_index1 = df.columns.get_loc('AREA') + 1
#         cell1= sheet.cell(row=row_index + 2, column=column_index1)

#         column_index2 = df.columns.get_loc('MUNICIPALITY') + 1
#         cell2= sheet.cell(row=row_index + 2, column=column_index2)
        
#         if compare_address(row["AREA"], row["ADDRESS"]):
#             cell1.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")

#         if compare_address(row["MUNICIPALITY"], row["ADDRESS"]):
#             cell2.fill = PatternFill(start_color="fffa00", end_color="fffa00", fill_type="solid")

#         if compare_address(row["MUNICIPALITY"], row["ADDRESS"]) and compare_address(row["AREA"], row["ADDRESS"]):
#             cell1.fill = PatternFill(start_color="ffa500", end_color="ffa500", fill_type="solid")
#             cell2.fill = PatternFill(start_color="ffa500", end_color="ffa500", fill_type="solid")

#     book.save('uploads\\new.xlsx')

# if __name__ == "__main__":
#     highlight_n_check_prediction('uploads\\Output-BPI-2024-03-19-0679.xlsx')

from fuzzywuzzy import fuzz
import re

def clean_string(input_string):
    # Define a regular expression pattern to match special characters
    pattern = r'[^a-zA-Z0-9\s]'
    
    # Use the sub() function from the re module to replace matched characters with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    
    return cleaned_string

def compare_string(str1, str2, threshold=80):
    similarity_ratio = fuzz.token_set_ratio(clean_string(str(str1)).lower(), clean_string(str(str2)).lower())
    print(similarity_ratio)
    return similarity_ratio >= threshold

# print(compare_string('address type', 'add type'))
# print(compare_string('address type', 'address'))
# print(compare_string('add', 'add type'))
# print(compare_string('dl type', 'add type'))
# # print(compare_string('add', 'address'))
# # print(compare_string('ch_code', 'ch code'))
# # print(compare_string('ch_name', 'ch code'))
# print(compare_string('REQUEST DATE', 'DATE REQUESTED'))
# print(compare_string('REQUEST NAME', 'DATE REQUESTED'))
# print(compare_string('REQUEST NAME', 'REQUESTED BY'))
# print(compare_string('REQUEST DATE', 'REQUESTED BY'))
# print(compare_string('AREA', 'FINAL AREA'))
print(compare_string('AUTOFIELD DATE', 'DATE'))

# template = pd.read_excel('source\\template.xlsx')

# print(template)

# import pandas as pd

# # Initialize an empty DataFrame
# empty_df = pd.DataFrame()

# # Add a column named 'column1' with values [1, 2, 3, 4, 5]
# empty_df['column1'] = [1, 2, 3, 4, 5]

# # print(empty_df)

# empty_df['column2'] = [1, 2, 3, 4, 5]

# # print(empty_df)

# new_df = pd.DataFrame()

# new_df = pd.concat([new_df, empty_df], ignore_index=True)
# print(new_df['column2'.upper()])

# columns = empty_df.columns.to_list()

# print(columns)

# import pandas as pd

# Create a DataFrame
data = {'column1': [1, 2, 3, 4, 5],
        'column2': [6, 7, 8, 9, 10]}

df = pd.DataFrame(data)

# Add a new column filled with empty strings
df['new_column'] = df['column1'].astype(str)

print(df)
