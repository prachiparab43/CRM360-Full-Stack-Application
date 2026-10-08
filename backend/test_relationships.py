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
    
    # 1. Fetch tables
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [row[0] for row in cursor.fetchall()]
    print("\n--- Current Tables in CRM360 ---")
    for table in sorted(tables):
        print(f"- {table}")
    
    # 2. Fetch Foreign Keys
    fk_query = """
    SELECT 
        fk.name AS fk_name,
        tp.name AS parent_table,
        tr.name AS referenced_table
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
    INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
    ORDER BY tp.name, fk.name
    """
    cursor.execute(fk_query)
    fks = cursor.fetchall()
    print("\n--- Foreign Key Constraints ---")
    for fk in fks:
        print(f"{fk.parent_table} -> {fk.referenced_table} ({fk.fk_name})")
    print("----------------------------------------------")

    conn.close()
except Exception as e:
    print(f"Error checking DB: {e}")
