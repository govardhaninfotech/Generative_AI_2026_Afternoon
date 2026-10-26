import sqlite3

# 1. Establish connection (creates 'company.db' if it doesn't exist)
# Use ':memory:' instead of a filename to test entirely in RAM
conn = sqlite3.connect("company.db")

# 2. Create a cursor object to execute commands
cursor = conn.cursor()

# 3. Create a table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        salary REAL
    )
""")

# 4. Insert data securely using '?' placeholders (prevents SQL Injection)
employee_data = ("Alice Smith", "Data Scientist", 95000.0)
cursor.execute(
    "INSERT INTO employees (name, role, salary) VALUES (?, ?, ?)", employee_data
)

# 5. Insert multiple records at once
more_employees = [
    ("Bob Jones", "UX Designer", 75000.0),
    ("Charlie Brown", "DevOps Engineer", 88000.0),
]
cursor.executemany(
    "INSERT INTO employees (name, role, salary) VALUES (?, ?, ?)",
    more_employees,
)

# 6. Save changes permanently to disk
conn.commit()

# 7. Query and retrieve data
cursor.execute("SELECT * FROM employees WHERE salary > ?", (80000.0,))
rows = cursor.fetchall()  # Returns a list of tuples

print("High earners:")
for row in rows:
    print(f"ID: {row[0]} | Name: {row[1]} | Role: {row[2]} | Salary: ${row[3]}")

# 8. Update data
cursor.execute(
    "UPDATE employees SET salary = ? WHERE name = ?", (98000.0, "Alice Smith")
)
conn.commit()

# 9. Delete data
cursor.execute("DELETE FROM employees WHERE name = ?", ("Bob Jones",))
conn.commit()

# 10. Clean up connections
cursor.close()
conn.close()