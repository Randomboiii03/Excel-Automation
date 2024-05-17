import psycopg2 

class DB:
    def __init__(self):
        self.conn = psycopg2.connect(database="geocode", user="postgres", password="1234", host="localhost", port="5432")
        self.cur = self.conn.cursor()

    def create(self):
        try:
            self.cur.execute("CREATE TABLE IF NOT EXISTS model (id serial PRIMARY KEY, area_muni VARCHAR(100), address VARCHAR(500));")
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            print("Error creating table:", e)
            return False

    def insert(self, df):
        try:
            area_munis, addresses = self.select()
            count = 0
            
            for _, row in df.iterrows():
                print(row)
                if (row['area-muni'] not in area_munis and row['address'] not in addresses):
                    query = "INSERT INTO model (area_muni, address) VALUES (%s, %s) ON CONFLICT DO NOTHING"
                    self.cur.execute(query, (row['area-muni'], row['address']))
                    count += 1

            self.conn.commit()
            return count
        except psycopg2.Error as e:
            print("Error inserting data:", e)
            return -1

    def select(self):
        try:
            self.cur.execute("SELECT area_muni, address FROM model")
            rows = self.cur.fetchall()
            area_munis = [row[0] for row in rows]
            addresses = [row[1] for row in rows]
            return area_munis, addresses
        except psycopg2.Error as e:
            print("Error selecting data:", e)
            return None, None

    def close(self):
        self.cur.close()
        self.conn.close()
