import psycopg2
import os

CONNECTION_STRING = "postgresql://neondb_owner:npg_8KFnZhaBb5sP@ep-crimson-sunset-apciwqz1.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"

def import_northwind():
    print("Reading northwind.sql...")
    with open("data/northwind.sql", "r", encoding="utf-8", errors="ignore") as f:
        sql = f.read()

    # Split into individual statements
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    print(f"Found {len(statements)} statements to execute")

    conn = psycopg2.connect(CONNECTION_STRING)
    conn.autocommit = True
    cursor = conn.cursor()

    success = 0
    failed = 0

    for i, statement in enumerate(statements):
        try:
            cursor.execute(statement)
            success += 1
            if success % 100 == 0:
                print(f"Progress: {success} statements executed...")
        except Exception as e:
            failed += 1

    cursor.close()
    conn.close()

    print(f"\nDone! {success} succeeded, {failed} failed")

if __name__ == "__main__":
    import_northwind()