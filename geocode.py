import pandas as pd
from tqdm import tqdm
import re
import json
import functions as func  # Importing custom functions
import sys
from threading import Thread
from multiprocessing import Process, Queue

class Geocode():
    def __init__(self, ):
        with open('source/address.json', 'r') as json_file:
            self.geocode_data = json.load(json_file)

        self.json_str_repr = json.dumps(self.geocode_data)

        self.zipcode_pattern = re.compile(r'(\d{4})( \S+)?$')
            
        self.count_not_found = 0  # Counter for not found addresses


    def check_address(self, place, search_term):
        return f"{place} " in f" {search_term} "

    
    def check_results(self, data, address):
        sublist_counts = {}
        for sublist in data:
            sublist_str = str(sublist)
            sublist_counts[sublist_str] = sublist_counts.get(sublist_str, 0) + 1
        
        highest_value = max(sublist_counts.values())
        most_common_sublist = [eval(key) for key, value in sublist_counts.items() if value == highest_value]
        
        if len(most_common_sublist) > 1:
            first_index_counts = {}
            for sublist in most_common_sublist:
                first_index_counts[sublist[0]] = first_index_counts.get(sublist[0], 0) + 1

            most_common_first_index = max(first_index_counts.values())
            filtered_data = [sublist for sublist in most_common_sublist for key, value in first_index_counts.items() if value == most_common_first_index and sublist[0] == key]

            if len(filtered_data) == 1:
                return filtered_data[0]
            
            most_common_muni = [area_muni for area_muni in filtered_data if area_muni[1] in address]
            
            if len(most_common_muni) == 1:
                return most_common_muni[0]
            else:
                closest_distance = len(address)
                closest_muni = None
                
                for muni in most_common_muni:
                    index = address.index(muni[1])
                    if index < closest_distance:
                        closest_distance = index
                        closest_muni = muni
                        
                return closest_muni
        else:
            return most_common_sublist[0]


    def search_zipcode(self, address):
        zipcode = self.zipcode_pattern.search(address)

        if zipcode:
            return zipcode.group(1)
        return None


    def check_duplicates_in_json(self, search_str):
        if search_str in self.json_str_repr:
            count = self.json_str_repr.count(search_str)
            return count > 1
        return False


    def check_in_data(self, index, orig_address):
        found_zipcode = self.search_zipcode(orig_address)
        orig_address = func.remove_numbers(orig_address)

        result_list = []

        for region, region_data in self.geocode_data.items():
            for province, municipalities in region_data.items():
                is_NCR = region == 'NCR'
                cleaned_province = func.clean_province(province) if not is_NCR else province
                
                if is_NCR:
                    if self.check_address(province, orig_address):
                        for municipality in municipalities:
                            if self.check_address(municipality.replace(' CITY', ''), orig_address):
                                result_list.append([region, province])
                else:
                    if self.check_address(cleaned_province, orig_address):
                        for municipality in municipalities:
                            cleaned_municipality = func.check_city(province, municipality)
                            if self.check_address(cleaned_municipality, orig_address):
                                result_list.append([province, municipality])

                for municipality, zipcode in municipalities.items():
                    if not is_NCR:
                        temp_municipality = func.check_city(province, municipality)
                        
                        if self.check_address(region, orig_address) and self.check_address(temp_municipality, orig_address):
                            result_list.append([province, municipality])

                        if not (self.check_duplicates_in_json(temp_municipality) or self.check_duplicates_in_json(municipality)) and self.check_address(temp_municipality, orig_address):
                            result_list.append([province, municipality])
                            
                    else:
                        if (not self.check_duplicates_in_json(province) or not self.check_duplicates_in_json(municipality)) and (self.check_address(province, orig_address) or self.check_address(municipality, orig_address)):
                            result_list.append([region, province])

                    if found_zipcode and found_zipcode == zipcode:
                        if not is_NCR:
                            result_list.append([province, municipality])
                        else:
                            result_list.append([region, province])


        print(f"#{index} - Address line: {orig_address} got {len(result_list)} result")
        
        if len(result_list) > 0:
            if len(result_list) == 1:
                return result_list[0]
            else:
                return self.check_results(result_list, orig_address)
            

        self.count_not_found += 1
        return None


    def search(self, index, orig_address, result_queue):
        result = self.check_in_data(index, func.clean_address(orig_address).upper())

        if result: 
            result_queue.put((index, result)) 

        result_queue.put((index, None)) 


    def main(self):
        df = pd.read_excel('source\\new_model.xlsx')

        addresses = df['address']
        predictions = [['', '']] * len(addresses)
        threads = []
        result_queue = Queue()

        for index, address in enumerate(addresses):
            if (len(address) >= 25):
                thread = Thread(target=self.search, args=(index, address, result_queue))
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

        temp_df = pd.DataFrame()
        temp_df['ADDRESS'] = df['address']

        while not result_queue.empty():
            index, result = result_queue.get()
            
            if result:
                print(type(result), result)
                predictions.insert(index, result)

        predictions_df = pd.DataFrame(predictions, columns=['AREA', 'MUNICIPALITY'])

        # Update temp_df with predictions
        temp_df[['AREA', 'MUNICIPALITY']] = predictions_df
        temp_df.to_excel('new_model2.xlsx', index=False)

if __name__ == '__main__':
    # If the script is run directly
    # if len(sys.argv) != 2:
    #     # Print usage if the number of arguments is incorrect
    #     print("Usage: python geocode.py <address>")
    #     sys.exit(1)
        
    # address = sys.argv[1]
    # # Search for the provided address and print the result
    # print(Geocode().check_in_data(0, address))
    
    Geocode().main()
