import psycopg2
import re

CONNECTION_STRING = "postgresql://neondb_owner:npg_8KFnZhaBb5sP@ep-crimson-sunset-apciwqz1.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"

def get_connection():
    return psycopg2.connect(CONNECTION_STRING)

def execute_with_retry(statements, label, batch_size=100):
    print(f"Importing {label}...")
    total = len(statements)
    success = 0
    
    for i in range(0, total, batch_size):
        batch = statements[i:i+batch_size]
        try:
            conn = get_connection()
            conn.autocommit = False
            cursor = conn.cursor()
            for stmt in batch:
                cursor.execute(stmt)
            conn.commit()
            cursor.close()
            conn.close()
            success += len(batch)
            print(f"  {label}: {success}/{total} rows done...")
        except Exception as e:
            print(f"  Batch failed: {e}")
            try:
                conn.rollback()
                conn.close()
            except:
                pass

    print(f"  {label} complete — {success} rows")

def parse_sql_file():
    with open("data/northwind.sql", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return content

def extract_section(content, table_name):
    """Extract all INSERT statements for a specific table."""
    pattern = rf"INSERT INTO {table_name}\b[^;]+;"
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    return matches

def extract_create_statements(content):
    """Extract all CREATE TABLE statements."""
    pattern = r"CREATE TABLE[^;]+;"
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    return matches

def extract_alter_statements(content):
    """Extract all ALTER TABLE statements."""
    pattern = r"ALTER TABLE[^;]+;"
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    return matches

def main():
    print("Reading SQL file...")
    content = parse_sql_file()

    # # Step 1: Drop and recreate schema
    # print("Resetting schema...")
    # conn = get_connection()
    # conn.autocommit = True
    # cursor = conn.cursor()
    # cursor.execute("DROP SCHEMA public CASCADE;")
    # cursor.execute("CREATE SCHEMA public;")
    # cursor.close()
    # conn.close()
    # print("Schema reset done")

    # # Step 2: Create all tables
    # create_stmts = extract_create_statements(content)
    # execute_with_retry(create_stmts, "CREATE TABLES")

    # Step 3: Import each table's data separately
    tables = [
        "categories",
        "customers",
        "customer_demographics",
        "customer_customer_demo",
        "employees",
        "employee_territories",
        "shippers",
        "suppliers",
        "products",
        "region",
        "territories",
        "us_states",
        "orders"
    ]

    for table in tables:
        inserts = extract_section(content, table)
        if inserts:
            execute_with_retry(inserts, f"{table} ({len(inserts)} rows)")
        else:
            print(f"  No data found for {table}")

    # Step 4: Add foreign keys
    alter_stmts = extract_alter_statements(content)
    execute_with_retry(alter_stmts, "FOREIGN KEYS")

    # Step 5: Verify
    print("\nVerifying import...")
    conn = get_connection()
    cursor = conn.cursor()
    for table in ["customers", "orders", "products", "order_details", "employees"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    cursor.close()
    conn.close()
    print("\nImport complete!")

if __name__ == "__main__":
    main()