"""Check actual test to see all unique table patterns"""
import re

# Replicate the EXACT test from test_extreme.py with 400 iterations
sql_parts = [
    "CREATE PROCEDURE dbo.EnterpriseDataWarehouse",
    "AS",
    "BEGIN",
]

for i in range(400):  # FULL 400 iterations like the real test
    sql_parts.extend([
        f"    BEGIN TRY",
        f"        WITH SalesCTE AS (SELECT * FROM Sales_{i % 10})",
        f"        UPDATE dbo.OrderSummary_{i % 5} SET X=1 FROM dbo.OrderSummary_{i % 5}",
        f"        INSERT INTO dbo.RegionalStats_{i % 3} SELECT * FROM Sales_{i % 10}",
        f"    END TRY",
        f"    BEGIN CATCH",
        f"    END CATCH",
    ])

sql_parts.extend([
    "    SELECT @Total = COUNT(*) FROM dbo.ProcessLog",
    "END"
])

sql = "\n".join(sql_parts)

# Extract all unique table patterns with regex
tables = set()
# FROM/JOIN/INTO/UPDATE patterns
for match in re.finditer(r'\b(?:FROM|JOIN|INTO|UPDATE)\s+([\w.]+)', sql, re.IGNORECASE):
    table = match.group(1)
    if '.' in table:
        table = table.split('.', 1)[1]
    if not table.startswith('@'):
        tables.add(table)

# CTEs
for match in re.finditer(r'WITH\s+(\w+)\s+AS', sql, re.IGNORECASE):
    tables.add(match.group(1))

print(f"Total unique tables: {len(tables)}")
print(f"Sorted: {sorted(tables)}")
