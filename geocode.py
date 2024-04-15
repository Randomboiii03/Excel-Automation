import pandas as pd
from tqdm import tqdm
import re
import json

class Geocode():
    def __init__(self):
        with open('source/all.json', 'r') as json_file:
            self.all_datas = json.load(json_file)

        with open('source/zipcode.json', 'r') as json_file:
            self.zipcode_data = json.load(json_file)

        with open('source/area_muni.json', 'r') as json_file:
            self.area_muni_data = json.load(json_file)

        with open('source/muni.json', 'r') as json_file:
            self.muni_data = json.load(json_file)

        self.df = pd.read_excel('WITHOUT AI.xlsx', usecols=['ADDRESS'])
        self.area_munis = [''] * len(self.df)

        self.count_not_found = 0

    def clean_address(self, address):
        address = re.sub(r"[^a-zA-Z0-9\s]", " ", address.upper().replace('Ñ', 'N')).split()
        return ' '.join(list(filter(lambda item: item.strip(), address)))

    def check_address(self, place, search_term):
        return f" {place} " in f" {search_term} "

    def search_zipcode(self, address):
        zipcode = re.search(r'(\d{4})( \S+)?$', address)

        if zipcode:
            return zipcode.group(1)
        
        return None

    def check_in_data(self, orig_address):
        for province in self.area_muni_data:
            if "SEARCH" in self.area_muni_data[province]:
                if self.check_address(self.area_muni_data[province]["SEARCH"], orig_address):
                    for municipality in self.area_muni_data[province]['MUNICIPALITIES']:
                        if self.check_address(municipality, orig_address):
                            return [province, municipality]

            if self.check_address(province, orig_address):
                for municipality in self.area_muni_data[province]['MUNICIPALITIES']:
                    if self.check_address(municipality, orig_address):
                        return [province, municipality]

        match_zipcode = self.search_zipcode(orig_address)

        if match_zipcode:
            for zipcode in self.zipcode_data:
                if match_zipcode == zipcode:
                    return [self.zipcode_data[str(zipcode)]['PROVINCE'], self.zipcode_data[str(zipcode)]['MUNICIPALITY']]

        for data in self.all_datas:
            region = data['REGION']
            province = data['PROVINCE']
            municipality = data['MUNICIPALITY']
            barangay = data['BARANGAY']
        
            if self.check_address(municipality, orig_address):
                if self.check_address(province, orig_address) or self.check_address(region, orig_address):
                    return [province, municipality]

        self.count_not_found += 1
        return None


    def search(self, orig_address):
        result = self.check_in_data(self.clean_address(orig_address).upper())

        if result: 
            # self.area_munis[index] = f"{result[0]}-{result[1]}"
            return result

        return None

                        
    def main(self):
        with tqdm(total=len(self.df['ADDRESS'])) as pbr:
            for index, orig_address in enumerate(self.df['ADDRESS']):
                self.search(index, orig_address)
                
                pbr.update(1)

        self.df["area-muni"] = self.area_munis
        self.df.to_excel('prediction.xlsx', index=False)

        print(f'Not Found: {self.count_not_found}\nFound: {len(self.area_munis) - self.count_not_found}')
        print('FINISHED')

if __name__ == '__main__':
    Geocode()

