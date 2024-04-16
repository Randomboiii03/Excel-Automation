import pandas as pd
from tqdm import tqdm
import re
import json

class Geocode():
    def __init__(self):
        with open('source/address.json', 'r') as json_file:
            self.geocode_data = json.load(json_file)

        self.df = pd.read_excel('WITHOUT AI.xlsx', usecols=['ADDRESS'])
        self.area_munis = [''] * len(self.df)

        self.count_not_found = 0

    def clean_address(self, address):
        address = re.sub(r"[^a-zA-Z0-9\s]", " ", address.upper().replace('Ñ', 'N')).split()

        abbreviation = {
            "GEN": "GENERAL",
            "STA": "SANTA",
            "STO": "SANTO",
        }

        for key, value in abbreviation.items():
            address = [value if word == key else word for word in address]

        return ' '.join(list(filter(lambda item: item.strip(), address)))

    def remove_numbers(self, address):
        return re.sub(r"\d+", "", address)


    def clean_province(self, province):
        suffix = ["DEL", "NORTE", "SUR", "DE ORO", "OCCIDENTAL", "ORIENTAL", "EASTERN", "NORTHERN", "SOUTHERN", "WESTERN", "NORTH", "SOUTH", "ISLAND"]
        
        province_parts = province.split()
        
        cleaned_province_parts = [part.strip() for part in province_parts if part.upper() not in suffix]
        
        cleaned_province = " ".join(cleaned_province_parts)
        
        return cleaned_province


    def check_address(self, place, search_term):
        return f" {place} " in f" {search_term} "


    def search_zipcode(self, address):
        zipcode = re.search(r'(\d{4})( \S+)?$', address)

        if zipcode:
            return zipcode.group(1)
        
        return None


    def check_in_data(self, orig_address):
        found_zipcode = self.search_zipcode(orig_address)
        orig_address = self.remove_numbers(orig_address)
        
        for region in self.geocode_data:
            if region == 'NCR':
                province = region

                if self.check_address(province, orig_address) or self.check_address("MANILA", orig_address):
                    for municipality in self.geocode_data[region]:
                        if self.check_address(municipality.replace(' CITY', ''), orig_address):
                            return [province, municipality]

                for municipality in self.geocode_data[region]:
                    if self.check_address(municipality, orig_address):
                        return [province, municipality]

            else:
                for province in self.geocode_data[region]:
                    if self.check_address(self.clean_province(province), orig_address):
                        for municipality in self.geocode_data[region][province]:
                            if self.check_address(municipality.replace(' CITY', ''), orig_address):
                                return [province, municipality]

                            if found_zipcode:
                                zipcode = self.geocode_data[region][province][municipality]
                                if found_zipcode == zipcode:
                                    return [province, municipality]

        for region in self.geocode_data:
            for municipality in self.geocode_data[region][province]:
                if found_zipcode:
                    zipcode = self.geocode_data[region][province][municipality]
                    if found_zipcode == zipcode:
                        return [province, municipality]

        self.count_not_found += 1
        return None


    def search(self, orig_address):
        result = self.check_in_data(self.clean_address(orig_address).upper())

        if result: 
            return result

        return None

                        
    def main(self):
        with tqdm(total=len(self.df['ADDRESS'])) as pbr:
            for index, orig_address in enumerate(self.df['ADDRESS']):
                result = self.check_in_data(self.clean_address(orig_address).upper())

                if result: 
                    self.area_munis[index] = f"{result[0]}-{result[1]}"
                
                pbr.update(1)

        self.df["area-muni"] = self.area_munis
        self.df.to_excel('prediction.xlsx', index=False)

        print(f'Not Found: {self.count_not_found}\nFound: {len(self.area_munis) - self.count_not_found}')
        print('FINISHED')

if __name__ == '__main__':
    # Geocode().main()
    print(Geocode().search('LOT 18 BLK 12 CHARITO HEIGHTS SUBD Ph 4 BRGY GRANADA BACOLOD CITY NEGROS OCCIDENTAL 5701'))


