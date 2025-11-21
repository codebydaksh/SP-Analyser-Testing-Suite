"""Debug script to understand table detection in the 2000-line monster test"""
import sys
sys.path.insert(0, 'src')
from parser.tsql_text_parser import TSQLTextParser

# Simplified version of the test
sql_parts = ["CREATE PROCEDURE dbo.Test AS BEGIN"]
for i in range(10):  # Just 10 iterations for debugging
    sql_parts.extend([
        f"WITH SalesCTE AS (SELECT * FROM Sales_{i % 10})",
        f"UPDATE dbo.OrderSummary_{i % 5} SET X=1",
        f"INSERT INTO dbo.RegionalStats_{i % 3} VALUES (1)",
        f"SELECT * FROM dbo.ProcessLog"
    ])
sql_parts.append("END")

sql = "\n".join(sql_parts)

parser = TSQLTextParser()
result = parser.parse(sql)

print(f"Total tables found: {len(result['tables'])}")
print(f"Tables: {result['tables']}")
print(f"\nBreakdown:")
print(f"  - CTEs (SalesCTE): {[t for t in result['tables'] if 'CTE' in t]}")
print(f"  - Sales_X: {[t for t in result['tables'] if t.startswith('Sales_')]}")
print(f"  - OrderSummary_X: {[t for t in result['tables'] if 'OrderSummary' in t]}")
print(f"  - RegionalStats_X: {[t for t in result['tables'] if 'RegionalStats' in t]}")
print(f"  - Other: {[t for t in result['tables'] if not any(x in t for x in ['CTE', 'Sales_', 'OrderSummary', 'RegionalStats'])]}")
