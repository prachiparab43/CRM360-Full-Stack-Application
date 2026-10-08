import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=DESKTOP-907QNQE;"
    "DATABASE=CRM360;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [row[0] for row in cursor.fetchall()]
    print("\n--- Verification: Created Tables in CRM360 ---")
    for table in tables:
        print(f"- {table}")
    print("----------------------------------------------")
    conn.close()
except Exception as e:
    print(f"Error verifying tables: {e}")
