import pandas as pd
from tqdm import tqdm
import re
import json
import functions as func
import sys

class Geocode():
    def __init__(self, ):
        with open('source/address.json', 'r') as json_file:
            self.geocode_data = json.load(json_file)
            
        self.count_not_found = 0


    def check_address(self, place, search_term):
        return f" {place} " in f" {search_term} "


    def search_zipcode(self, address):
        zipcode = re.search(r'(\d{4})( \S+)?$', address)

        if zipcode:
            return zipcode.group(1)
        
        return None


    def check_in_data(self, orig_address):
        found_zipcode = self.search_zipcode(orig_address)
        orig_address = func.remove_numbers(orig_address)
        
        for region in self.geocode_data:
            if region == 'NCR':
                province = region

                if self.check_address(province, orig_address):
                    for municipality in self.geocode_data[region]:
                        if self.check_address(municipality.replace(' CITY', ''), orig_address):
                            return [province, municipality]
                    
                    for municipality in self.geocode_data[region]:
                        for submuni in self.geocode_data[region][municipality]:
                            if self.check_address(submuni, orig_address):
                                return [province, municipality]

                # for municipality in self.geocode_data[region]:
                #     if self.check_address(municipality, orig_address):
                #         return [province, municipality]

            else:
                for province in self.geocode_data[region]:
                    if self.check_address(func.clean_province(province), orig_address):
                        for municipality in self.geocode_data[region][province]:
                            if self.check_address(municipality, orig_address):
                                return [province, municipality]

        for region in self.geocode_data:
            for province in self.geocode_data[region]:
                for municipality in self.geocode_data[region][province]:
                    if found_zipcode:
                        zipcode = self.geocode_data[region][province][municipality]
                        if found_zipcode == zipcode:
                            if region == "NCR":
                                return [region, province]
                            else:
                                return [province, municipality]

        self.count_not_found += 1
        return None


    def search(self, orig_address):
        result = self.check_in_data(func.clean_address(orig_address).upper())

        if result: 
            return result

        return None

if __name__ == '__main__':
    # Geocode().main()
    if len(sys.argv) != 2:
        print("Usage: python geocode.py <address>")
        sys.exit(1)

    address = sys.argv[1]
    print(Geocode().search(address))


