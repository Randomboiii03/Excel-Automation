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

        # self.df = pd.read_excel('test.xlsx', usecols=['ADDRESS'])
        # self.area_munis = [''] * len(self.df)

        self.count_not_found = 0

    def clean_address(self, address):
        address = re.sub(r"[^a-zA-Z0-9\s]", " ", address.upper().replace('Ñ', 'N')).split()
        return ' '.join(list(filter(lambda item: item.strip(), address)))

    def check_address(self, place, search_term):
        return place.replace(' ', '') in search_term or place in search_term

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
                
                for barangay in self.area_muni_data[province]['BARANGAYS']:
                    for key, value in barangay.items():
                        if self.check_address(key, orig_address):
                            return [province, value]

        for zipcode in self.zipcode_data:
            if self.check_address(zipcode, orig_address):
                return [self.zipcode_data[str(zipcode)]['PROVINCE'], self.zipcode_data[str(zipcode)]['MUNICIPALITY']]

        for data in self.all_datas:
            region = data['REGION']
            province = data['PROVINCE']
            municipality = data['MUNICIPALITY']
            barangay = data['BARANGAY']
        
            if self.check_address(f" {municipality} ", f" {orig_address} "):
                if self.check_address(province, orig_address) or (self.check_address(barangay, orig_address) or self.check_address(region, orig_address)):
                    return [province, municipality]

        for data in self.muni_data:
            province = data['PROVINCE']
            municipality = data['MUNICIPALITY'].replace('C', 'K')
            
            if 'SEARCH' in data:
                for search in data['SEARCH']:
                    if self.check_address(f" {search.replace('C', 'K')} ", f" {orig_address.replace('C', 'K')} "):
                        return [province, municipality]

            if self.check_address(f" {municipality} ", f" {orig_address.replace('C', 'K')} "):
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

