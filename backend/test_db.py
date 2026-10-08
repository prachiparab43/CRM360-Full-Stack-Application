import pyodbc

# Test connection to master to check/create CRM360 database
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=DESKTOP-907QNQE;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

try:
    print("Connecting to master database...")
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("SELECT 1 successful! Windows Authentication works.")
    
    cursor.execute("SELECT name FROM sys.databases WHERE name = 'CRM360'")
    if cursor.fetchone():
        print("Database 'CRM360' already exists.")
    else:
        print("Database 'CRM360' does not exist. Creating it now...")
        cursor.execute("CREATE DATABASE CRM360")
        print("Database 'CRM360' created successfully.")
    
    conn.close()
except Exception as e:
    print(f"Error during database check: {e}")
