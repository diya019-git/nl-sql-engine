import subprocess
import sys

CONNECTION_STRING = "postgresql://neondb_owner:npg_8KFnZhaBb5sP@ep-crimson-sunset-apciwqz1.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"

def import_northwind():
    print("Starting import...")
    
    with open("data/northwind.sql", "rb") as f:
        sql_content = f.read()
    
    result = subprocess.run(
        ["psql", CONNECTION_STRING, "--set=ON_ERROR_STOP=off"],
        input=sql_content,
        capture_output=True
    )
    
    output = result.stdout.decode("utf-8", errors="ignore")
    errors = result.stderr.decode("utf-8", errors="ignore")
    
    print("Output (last 20 lines):")
    lines = output.strip().split("\n")
    for line in lines[-20:]:
        print(line)
    
    if errors:
        print("\nErrors (last 5 lines):")
        err_lines = errors.strip().split("\n")
        for line in err_lines[-5:]:
            print(line)

if __name__ == "__main__":
    import_northwind()