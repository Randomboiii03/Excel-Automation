import psycopg2 
from dotenv import load_dotenv
import os

class DB:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Retrieve database connection parameters from environment variables
        DB_NAME = os.getenv('DB_NAME')
        USER_NAME = os.getenv('USER_NAME')
        PASSWORD = os.getenv('PASSWORD')
        HOST_NAME = os.getenv('HOST_NAME')
        PORT = os.getenv('PORT')

        # Establish a connection to the PostgreSQL database
        self.conn = psycopg2.connect(database=DB_NAME, user=USER_NAME, password=PASSWORD, host=HOST_NAME, port=PORT)
        # Create a cursor object to execute PostgreSQL commands
        self.cur = self.conn.cursor()

    def create(self):
        try:
            # Create a table named 'model' if it doesn't exist already
            self.cur.execute("CREATE TABLE IF NOT EXISTS model (id serial PRIMARY KEY, area_muni VARCHAR(100), address VARCHAR(500));")
            # Commit the transaction
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error creating table:", e)
            return False

    def insert(self, df):
        try:
            # Retrieve existing area_munis and addresses from the database
            area_munis, addresses = self.select()
            # Initialize count for counting successful insertions
            count = 0
            
            # Iterate through each row in the DataFrame
            for _, row in df.iterrows():
                # Check if the area-muni and address combination is not already present in the database
                if (row['area-muni'] not in area_munis and row['address'] not in addresses):
                    # SQL query to insert data into the 'model' table, ignoring conflicts
                    query = "INSERT INTO model (area_muni, address) VALUES (%s, %s) ON CONFLICT DO NOTHING"
                    # Execute the query with the values from the DataFrame
                    self.cur.execute(query, (row['area-muni'], row['address']))
                    # Increment count for successful insertion
                    count += 1

            # Commit the transaction
            self.conn.commit()
            return count
        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error inserting data:", e)
            return -1

    def select(self):
        try:
            # Execute SQL query to select all area_muni and address pairs from the 'model' table
            self.cur.execute("SELECT area_muni, address FROM model")

            # Fetch all rows from the result
            rows = self.cur.fetchall()
            # Extract area_munis and addresses from the fetched rows
            area_munis = [row[0] for row in rows]
            addresses = [row[1] for row in rows]
            
            return area_munis, addresses

        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error selecting data:", e)
            return None, None

    def close(self):
        # Close the cursor
        self.cur.close()
        # Close the database connection
        self.conn.close()