import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os
import sys
import functions as func

class DB:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Retrieve database connection parameters from environment variables
        self.DB_NAME = os.getenv('DB_NAME')
        self.USER_NAME = os.getenv('USER_NAME')
        self.PASSWORD = os.getenv('PASSWORD')
        self.HOST_NAME = os.getenv('HOST_NAME')
        self.PORT = os.getenv('PORT')

        self.connection_pool = None
        self.init_pool()

    def init_pool(self):
        try:
            # Create a connection pool
            self.connection_pool = pool.SimpleConnectionPool(1, 10,
                database=self.DB_NAME,
                user=self.USER_NAME,
                password=self.PASSWORD,
                host=self.HOST_NAME,
                port=self.PORT
            )
        except psycopg2.Error as e:
            print("Error initializing connection pool:", e)

    def get_connection(self):
        try:
            # Acquire a connection from the pool
            return self.connection_pool.getconn()
        except psycopg2.Error as e:
            print("Error getting connection from pool:", e)
            return None

    def release_connection(self, conn):
        try:
            # Release the connection back to the pool
            self.connection_pool.putconn(conn)
        except psycopg2.Error as e:
            print("Error releasing connection to pool:", e)

    def close_pool(self):
        try:
            # Close all connections in the pool
            self.connection_pool.closeall()
        except psycopg2.Error as e:
            print("Error closing connection pool:", e)

    def create(self):
        conn = None
        try:
            # Acquire a connection from the pool
            conn = self.get_connection()
            if conn:
                # Create a cursor object to execute PostgreSQL commands
                cur = conn.cursor()
                # Create a table named 'model' if it doesn't exist already
                cur.execute("""
                    CREATE EXTENSION IF NOT EXISTS pg_trgm;
                    CREATE TABLE IF NOT EXISTS model (id serial PRIMARY KEY, area_muni VARCHAR(100), address VARCHAR(500));
                """)
                # Commit the transaction
                conn.commit()
                # Return the cursor to the pool
                self.release_connection(conn)
                return True
            else:
                return False
        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error creating table:", e)
            if conn:
                # Rollback any changes if an error occurred
                conn.rollback()
            return False


    def create_index(self):
        conn = None
        try:
            # Acquire a connection from the pool
            conn = self.get_connection()
            if conn:
                # Create a cursor object to execute PostgreSQL commands
                cur = conn.cursor()
                # SQL query to create an index on the 'area_muni' and 'address' columns
                query = "CREATE INDEX IF NOT EXISTS trgm_idx ON model USING GIST (address gist_trgm_ops);"
                # Execute the query
                cur.execute(query)
                # Commit the transaction
                conn.commit()
                # Print a message indicating the index creation
                print("Index created successfully")
            else:
                print("No connection available")
        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error creating index:", e)
            if conn:
                # Rollback any changes if an error occurred
                conn.rollback()
        finally:
            if conn:
                # Release the connection back to the pool
                self.release_connection(conn)


    def insert(self, df):
        conn = None
        try:
            # Acquire a connection from the pool
            conn = self.get_connection()
            if conn:
                # Create a cursor object to execute PostgreSQL commands
                cur = conn.cursor()
                # Retrieve existing area_munis and addresses from the database
                area_munis, addresses = self.select(cur)
                # Initialize count for counting successful insertions
                count = 0

                # Iterate through each row in the DataFrame
                for _, row in df.iterrows():
                    # Check if the area-muni and address combination is not already present in the database
                    if (row['area-muni'] not in area_munis and row['address'] not in addresses and len(func.remove_numbers(row['address'])) > 20 ):
                        # SQL query to insert data into the 'model' table, ignoring conflicts
                        query = "INSERT INTO model (area_muni, address) VALUES (%s, %s) ON CONFLICT DO NOTHING"
                        # Execute the query with the values from the DataFrame
                        cur.execute(query, (row['area-muni'], func.remove_numbers(row['address'])))
                        # Increment count for successful insertion
                        count += 1

                # Commit the transaction
                conn.commit()
                # Return the cursor to the pool
                self.release_connection(conn)
                return count
            else:
                return -1
        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error inserting data:", e)
            if conn:
                # Rollback any changes if an error occurred
                conn.rollback()
            return -1


    def select(self, cur):
        try:
            # Execute SQL query to select all area_muni and address pairs from the 'model' table
            cur.execute("SELECT area_muni, address FROM model")

            # Fetch all rows from the result
            rows = cur.fetchall()
            # Extract area_munis and addresses from the fetched rows
            area_munis = [row[0] for row in rows]
            addresses = [row[1] for row in rows]

            return area_munis, addresses

        except psycopg2.Error as e:
            # If an error occurs, print the error message
            print("Error selecting data:", e)
            return None, None


    def search_address(self, address):
        conn = None
        try:
            # Acquire a connection from the pool
            conn = self.get_connection()
            if conn:
                # Create a cursor object to execute PostgreSQL commands
                cur = conn.cursor()

                sql = """
                    SELECT area_muni, SIMILARITY(address, %s) * 100 AS similarity_percentage
                    FROM model
                    ORDER BY similarity_percentage DESC
                    LIMIT 10;
                    """

                cur.execute(sql, (address,))

                rows = cur.fetchall()

                area_muni_list = [row[0] for row in rows]
                similarity_percentage = [row[1] for row in rows]

                indices_greater_than_50 = [i for i, score in enumerate(similarity_percentage) if score >= 40.0]

                if indices_greater_than_50:
                    highest_index = max(indices_greater_than_50, key=lambda x: similarity_percentage[x])

                    return area_muni_list[highest_index], similarity_percentage[highest_index]

                else:
                    most_common_area_muni = max(area_muni_list, key=area_muni_list.count)

                    return most_common_area_muni, similarity_percentage[area_muni_list.index(most_common_area_muni)]
            else:
                print("No connection available")
                return None

        except psycopg2.Error as e:
            print("Error selecting data:", e)
            return None
        finally:
            if conn:
                # Release the connection back to the pool
                self.release_connection(conn)

if __name__ == '__main__':
    # If the script is run directly
    if len(sys.argv) != 2:
        # Print usage if the number of arguments is incorrect
        print("Usage: python geocode.py <address>")
        sys.exit(1)

    address = sys.argv[1]
    db = DB()
    db.create_index()
    # Search for the provided address and print the result
    print(db.search_address(address))


# CREATE INDEX idx_model_location ON model(area_muni, address);
# PREPARE stmt AS
# SELECT area_muni, address, MAX(SIMILARITY(address, $1)) * 100 AS similarity_percentage
# FROM model
# GROUP BY area_muni, address
# ORDER BY similarity_percentage DESC
# LIMIT 10;

# EXECUTE stmt ('OURBLEND COFFEE AND MILKTEA TALABASUPER 9 BLDG EMILIO AGUINALDO HIGHWAYTALABA 7');

