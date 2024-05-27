from database import DB as db

area_munis, addresses = db().select()
temp = [tuple(area_muni.split('-', 1)) for area_muni in area_munis]

area, muni = zip(*temp)

print(area)
# print(muni)