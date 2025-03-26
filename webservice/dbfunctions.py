import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# Create a database connection
def connectDatabase():
    conn = psycopg2.connect(
        host=os.getenv('DBHOST'),
        database=os.getenv('DBNAME'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWORD'),
        port=os.getenv('DBPORT'),)
    conn.autocommit = True
    cursor = conn.cursor()
    return cursor

# Execute database query
def executeQuery(query):
    conn = connectDatabase()
    conn.execute(query)
    result = conn.fetchall()
    return result

# Execute database query without fetching data
def executeWithoutFetch(query):
    conn = connectDatabase()
    conn.execute(query)
    return None

def bulkInsert(query, data):
    conn = connectDatabase()
    return execute_values(conn, query, data)