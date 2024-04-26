import pandas as pd
from tqdm import tqdm
import re
import json
import functions as func  # Importing custom functions
import sys

class Geocode():
    def __init__(self, ):
        # Initialize Geocode class
        # Load geocode data from JSON file
        with open('source/address.json', 'r') as json_file:
            self.geocode_data = json.load(json_file)
            
        self.count_not_found = 0  # Counter for not found addresses

    def check_address(self, place, search_term):
        """
        Check if a place is present in the search term.

        Args:
            place (str): Place to search for.
            search_term (str): Search term.

        Returns:
            bool: True if place is present in search term, False otherwise.
        """
        return f" {place} " in f" {search_term} "

    def search_zipcode(self, address):
        """
        Search for a zipcode in the address.

        Args:
            address (str): Address to search for the zipcode.

        Returns:
            str: Zipcode if found, None otherwise.
        """
        zipcode = re.search(r'(\d{4})( \S+)?$', address)

        if zipcode:
            return zipcode.group(1)
        
        return None

    def slice_address(self, string, num):
        length = len(string)
        three_fourths_length = length * num // 4
        three_fourths_string = string[three_fourths_length:]
        return three_fourths_string

    def check_in_data(self, orig_address):
        """
        Check if the address is in the geocode data.

        Args:
            orig_address (str): Original address to search for.

        Returns:
            list or None: List containing region, province, and municipality if found, None otherwise.
        """
        found_zipcode = self.search_zipcode(orig_address)
        temp_address = func.remove_numbers(orig_address)

        for i in range(3, -1, -1):
            orig_address = self.slice_address(temp_address, i)
            print(orig_address)

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
        """
        Perform the address search.

        Args:
            orig_address (str): Original address to search for.

        Returns:
            list or None: List containing region, province, and municipality if found, None otherwise.
        """
        result = self.check_in_data(func.clean_address(orig_address).upper())

        if result: 
            return result

        return None

if __name__ == '__main__':
    # If the script is run directly
    if len(sys.argv) != 2:
        # Print usage if the number of arguments is incorrect
        print("Usage: python geocode.py <address>")
        sys.exit(1)

    address = sys.argv[1]
    # Search for the provided address and print the result
    print(Geocode().search(address))
