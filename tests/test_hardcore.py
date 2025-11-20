import pytest
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser.tsql_text_parser import TSQLTextParser
from analyzer.security_analyzer import SecurityAnalyzer
from analyzer.quality_analyzer import CodeQualityAnalyzer
from analyzer.performance_analyzer import PerformanceAnalyzer
from analyzer.cfg_builder import CFGBuilder

# ===== HARDCORE TEST SUITE =====

def test_massive_1500_line_sp():
    """Test 1: Handle massive 1500+ line stored procedure."""
    # Generate massive realistic SP
    lines = [
        "CREATE PROCEDURE dbo.MassiveDataProcessor",
        "    @StartDate DATETIME,",
        "    @EndDate DATETIME,",
        "    @BatchSize INT = 1000",
        "AS",
        "BEGIN",
        "    SET NOCOUNT ON;",
        "    DECLARE @Counter INT = 0;",
        "    DECLARE @TotalRecords INT;",
        ""
    ]
    
    # Add complex business logic (1500+ lines)
    for i in range(300):
        lines.extend([
            f"    -- Processing batch {i}",
            "    BEGIN TRY",
            "        IF @Counter < @TotalRecords",
            "        BEGIN",
            f"            SELECT * FROM Orders_{i % 10} WHERE OrderDate >= @StartDate",
            f"            UPDATE OrderStats_{i % 5} SET ProcessedFlag = 1",
            "        END",
            "    END TRY",
            "    BEGIN CATCH",
            "        ROLLBACK TRAN",
            "        THROW;",
            "    END CATCH",
            ""
        ])
    
    lines.append("END")
    sql = "\n".join(lines)
    
    start = time.time()
    parser = TSQLTextParser()
    result = parser.parse(sql)
    elapsed = time.time() - start
    
    # Performance requirements
    assert elapsed < 2.0,f"Parsing 1500+ lines took {elapsed}s (should be < 2s)"
    assert result['lines_of_code'] > 1000
    assert len(result['tables']) > 10
    print(f"✅ Handled {result['lines_of_code']} LOC in {elapsed:.3f}s")

def test_deeply_nested_control_flow():
    """Test 2: Handle deeply nested IF/WHILE/CASE (10 levels deep)."""
    sql = """
    CREATE PROCEDURE dbo.DeepNesting AS
    BEGIN
        IF @L1 = 1 BEGIN
            IF @L2 = 1 BEGIN
                IF @L3 = 1 BEGIN
                    IF @L4 = 1 BEGIN
                        IF @L5 = 1 BEGIN
                            IF @L6 = 1 BEGIN
                                IF @L7 = 1 BEGIN
                                    IF @L8 = 1 BEGIN
                                        IF @L9 = 1 BEGIN
                                            IF @L10 = 1 BEGIN
                                                SELECT 'MAX DEPTH'
                                            END
                                        END
                                    END
                                END
                            END
                        END
                    END
                END
            END
        END
    END
    """
    
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql)
    assert len(cfg.nodes) > 10
    print(f"✅ Built CFG with {len(cfg.nodes)} nodes for 10-level nesting")

def test_extreme_parameter_count():
    """Test 3: Handle SP with 50+ parameters."""
    params = [f"@Param{i} VARCHAR(100) = NULL" for i in range(50)]
    sql = f"""
    CREATE PROCEDURE dbo.ManyParams
        {', '.join(params)}
    AS
    SELECT 1
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'parameters' in result
    print(f"✅ Parsed SP with 50 parameters")

def test_complex_dynamic_sql_injection():
    """Test 4: Detect sophisticated SQL injection patterns."""
    sqls = [
        # Pattern 1: String building
        "DECLARE @SQL NVARCHAR(MAX) = 'SELECT * FROM Users WHERE Name = ''' + @UserInput + ''''; EXEC(@SQL)",
        
        # Pattern 2: sp_executesql
        "EXEC sp_executesql N'SELECT * FROM Orders WHERE UserId = ' + CAST(@UserId AS VARCHAR)",
        
        # Pattern 3: Hidden concatenation
        "SET @Query = @BaseQuery + ' AND Username = ''' + @Username + ''''; EXECUTE(@Query)",
        
        # Pattern 4: Multi-step
        "SET @Part1 = 'SELECT '; SET @Part2 = @Columns + ' FROM Users'; EXEC(@Part1 + @Part2)"
    ]
    
    analyzer = SecurityAnalyzer()
    for sql in sqls:
        result = analyzer.analyze(sql)
        assert len(result['sql_injection_risks']) > 0, f"Failed to detect: {sql[:50]}"
    
    print(f"✅ Detected {len(sqls)} sophisticated SQL injection patterns")

def test_all_tsql_data_types():
    """Test 5: Handle all T-SQL data types."""
    data_types = [
        "BIGINT", "INT", "SMALLINT", "TINYINT", "BIT",
        "DECIMAL(18,4)", "NUMERIC(10,2)", "MONEY", "SMALLMONEY",
        "FLOAT", "REAL",
        "DATE", "TIME", "DATETIME", "DATETIME2", "SMALLDATETIME", "DATETIMEOFFSET",
        "CHAR(10)", "VARCHAR(MAX)", "TEXT", "NCHAR(10)", "NVARCHAR(MAX)", "NTEXT",
        "BINARY(50)", "VARBINARY(MAX)", "IMAGE",
        "UNIQUEIDENTIFIER", "XML", "SQL_VARIANT",
        "GEOGRAPHY", "GEOMETRY", "HIERARCHYID"
    ]
    
    params = [f"@P{i} {dt}" for i, dt in enumerate(data_types)]
    sql = f"CREATE PROCEDURE dbo.AllTypes {', '.join(params)} AS SELECT 1"
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert result is not None
    print(f"✅ Handled {len(data_types)} different T-SQL data types")

def test_multiple_result_sets():
    """Test 6: Handle SP with multiple result sets."""
    sql = """
    CREATE PROCEDURE dbo.MultiResults AS
    BEGIN
        SELECT * FROM Users
        SELECT * FROM Orders
        SELECT * FROM Products
        SELECT * FROM Invoices
        SELECT * FROM Customers
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    tables = result['tables']
    assert len(tables) >= 5
    print(f"✅ Parsed SP with {len(tables)} result sets")

def test_temp_table_heavy_sp():
    """Test 7: Handle SP with multiple temp tables."""
    sql = """
    CREATE PROCEDURE dbo.TempTableHeavy AS
    BEGIN
        CREATE TABLE #Temp1 (Id INT)
        CREATE TABLE ##GlobalTemp (Name VARCHAR(50))
        CREATE TABLE #Temp2 (Data XML)
        
        INSERT INTO #Temp1 SELECT 1
        SELECT * FROM #Temp1 t1 JOIN ##GlobalTemp gt ON t1.Id = gt.Id
        
        DROP TABLE #Temp1
        DROP TABLE ##GlobalTemp
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert '#Temp1' in result['tables'] or 'Temp1' in str(result['tables'])
    print("✅ Handled temp tables correctly")

def test_cte_and_subqueries():
    """Test 8: Handle complex CTEs and subqueries."""
    sql = """
    CREATE PROCEDURE dbo.ComplexCTE AS
    BEGIN
        ;WITH CTE1 AS (
            SELECT * FROM Orders WHERE Status = 'Active'
        ),
        CTE2 AS (
            SELECT * FROM CTE1 WHERE Amount > 100
        ),
        RecursiveCTE AS (
            SELECT Id, ParentId, 1 AS Level FROM Categories WHERE ParentId IS NULL
            UNION ALL
            SELECT c.Id, c.ParentId, r.Level + 1
            FROM Categories c
            JOIN RecursiveCTE r ON c.ParentId = r.Id
        )
        SELECT * FROM RecursiveCTE
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'Orders' in result['tables']
    assert 'Categories' in result['tables']
    print("✅ Parsed complex CTEs and recursive queries")

def test_error_handling_patterns():
    """Test 9: Detect missing error handling."""
    good_sql = """
    BEGIN TRY
        BEGIN TRAN
        UPDATE Orders SET Status = 'Processed'
        COMMIT TRAN
    END TRY
    BEGIN CATCH
        ROLLBACK TRAN
        THROW;
    END CATCH
    """
    
    bad_sql = """
    BEGIN TRAN
    UPDATE Orders SET Status = 'Processed'
    COMMIT TRAN
    """
    
    analyzer = SecurityAnalyzer()
    
    good_result = analyzer.analyze(good_sql)
    bad_result = analyzer.analyze(bad_sql)
    
    assert analyzer.get_security_score(good_sql) > analyzer.get_security_score(bad_sql)
    print("✅ Detected missing error handling")

def test_performance_anti_patterns():
    """Test 10: Detect ALL performance anti-patterns."""
    anti_patterns = [
        ("Cursor", "DECLARE c CURSOR FOR SELECT * FROM Users; OPEN c; FETCH NEXT FROM c"),
        ("Implicit conversion", "SELECT * FROM Users WHERE UserId = '123'"),
        ("UPPER function", "SELECT * FROM Users WHERE UPPER(Name) = 'JOHN'"),
        ("Multiple ORs", "WHERE Col = 'A' OR Col = 'B' OR Col = 'C' OR Col = 'D' OR Col = 'E'"),
        ("Leading wildcard", "WHERE Name LIKE '%Smith'"),
        ("SELECT INTO", "SELECT * INTO NewTable FROM OldTable")
    ]
    
    analyzer = PerformanceAnalyzer()
    
    for name, sql in anti_patterns:
        result = analyzer.analyze(sql)
        assert len(result['issues']) > 0, f"Failed to detect: {name}"
    
    print(f"✅ Detected all {len(anti_patterns)} performance anti-patterns")

def test_transaction_nesting():
    """Test 11: Handle nested transactions."""
    sql = """
    BEGIN TRAN OuterTran
        UPDATE Table1 SET Col = 1
        
        SAVE TRAN SavePoint1
        UPDATE Table2 SET Col = 2
        
        IF @@ERROR <> 0
            ROLLBACK TRAN SavePoint1
        ELSE
            COMMIT TRAN OuterTran
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert result['has_transaction'] == True
    print("✅ Parsed nested transactions")

def test_unicode_and_special_chars():
    """Test 12: Handle Unicode and special characters."""
    sql = """
    CREATE PROCEDURE dbo.UnicodeTest
        @Name NVARCHAR(100) = N'测试者'
    AS
    BEGIN
        SELECT * FROM Users WHERE Name = @Name
        -- Comment with émojis: 🎉 ✅ 🚀
        PRINT N'Success: 成功'
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert result is not None
    print("✅ Handled Unicode and special characters")

def test_all_join_types():
    """Test 13: Detect all JOIN types."""
    sql = """
    SELECT *
    FROM Table1 t1
    INNER JOIN Table2 t2 ON t1.Id = t2.Id
    LEFT JOIN Table3 t3 ON t1.Id = t3.Id
    RIGHT JOIN Table4 t4 ON t1.Id = t4.Id
    FULL OUTER JOIN Table5 t5 ON t1.Id = t5.Id
    CROSS JOIN Table6 t6
    CROSS APPLY fn_Split(t1.Data) t7
    OUTER APPLY fn_Parse(t1.Json) t8
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert len(result['tables']) >= 6
    print(f"✅ Parsed {len(result['tables'])} tables with various JOIN types")

def test_merge_statement():
    """Test 14: Handle MERGE statements."""
    sql = """
    MERGE INTO Target t
    USING Source s ON t.Id = s.Id
    WHEN MATCHED THEN
        UPDATE SET t.Value = s.Value
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (Id, Value) VALUES (s.Id, s.Value)
    WHEN NOT MATCHED BY SOURCE THEN
        DELETE;
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    tables = result['tables']
    assert 'Target' in tables or 'Source' in tables
    print("✅ Parsed MERGE statement")

def test_xml_and_json_operations():
    """Test 15: Handle XML/JSON operations."""
    sql = """
    CREATE PROCEDURE dbo.XmlJsonTest AS
    BEGIN
        DECLARE @xml XML = '<root><item>1</item></root>'
        DECLARE @json NVARCHAR(MAX) = '{"key": "value"}'
        
        SELECT @xml.value('(/root/item)[1]', 'INT')
        SELECT JSON_VALUE(@json, '$.key')
        
        SELECT * FROM OPENJSON(@json)
        SELECT * FROM Users FOR XML AUTO
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert result is not None
    print("✅ Parsed XML/JSON operations")

def test_window_functions():
    """Test 16: Handle window functions."""
    sql = """
    SELECT
        ROW_NUMBER() OVER (ORDER BY Id) AS RowNum,
        RANK() OVER (PARTITION BY Category ORDER BY Sales DESC) AS SalesRank,
        LAG(Sales) OVER (ORDER BY Date) AS PrevSales,
        LEAD(Sales) OVER (ORDER BY Date) AS NextSales
    FROM SalesData
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'SalesData' in result['tables']
    print("✅ Parsed window functions")

def test_pivot_and_unpivot():
    """Test 17: Handle PIVOT/UNPIVOT."""
    sql = """
    SELECT * FROM
    (SELECT Year, Quarter, Sales FROM QuarterlyData) AS SourceTable
    PIVOT (SUM(Sales) FOR Quarter IN ([Q1], [Q2], [Q3], [Q4])) AS PivotTable
    
    SELECT * FROM
    (SELECT Year, Q1, Q2, Q3, Q4 FROM AnnualData) AS SourceTable
    UNPIVOT (Sales FOR Quarter IN (Q1, Q2, Q3, Q4)) AS UnpivotTable
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert len(result['tables']) > 0
    print("✅ Parsed PIVOT/UNPIVOT operations")

def test_output_clause():
    """Test 18: Handle OUTPUT clause."""
    sql = """
    UPDATE Orders
    SET Status = 'Processed'
    OUTPUT DELETED.OrderId, DELETED.Status AS OldStatus,
           INSERTED.OrderId, INSERTED.Status AS NewStatus
    INTO OrderHistory
    WHERE OrderDate < GETDATE()
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'Orders' in result['tables']
    print("✅ Parsed OUTPUT clause")

def test_indexed_views_and_computed_columns():
    """Test 19: Handle indexed views."""
    sql = """
    SELECT * FROM dbo.vw_OrderSummary WITH (NOEXPAND)
    WHERE TotalAmount > (SELECT AVG(TotalAmount) FROM dbo.vw_OrderSummary)
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert len(result['tables']) > 0
    print("✅ Parsed indexed views")

def test_try_convert_and_isnull():
    """Test 20: Handle TRY_CONVERT, ISNULL, COALESCE."""
    sql = """
    SELECT
        TRY_CONVERT(INT, StringColumn) AS ConvertedInt,
        ISNULL(NullableColumn, 'Default') AS WithDefault,
        COALESCE(Col1, Col2, Col3, 'Final Default') AS FirstNonNull,
        TRY_CAST(DateString AS DATE) AS ConvertedDate
    FROM MixedData
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'MixedData' in result['tables']
    print("✅ Parsed TRY_CONVERT and COALESCE")

def test_batch_quality_scoring():
    """Test 21: Batch quality analysis stress test."""
    test_cases = []
    
    # Generate 50 SPs with varying quality
    for i in range(50):
        quality = (i % 5) + 1  # 1-5 quality levels
        
        if quality == 5:
            sql = f"""
            CREATE PROCEDURE sp{i} AS
            SET NOCOUNT ON;
            BEGIN TRY
                BEGIN TRAN
                SELECT Id, Name FROM dbo.Table{i} WHERE Id = @Id
                COMMIT TRAN
            END TRY
            BEGIN CATCH
                ROLLBACK TRAN
                THROW;
            END CATCH
            """
        else:
            sql = f"CREATE PROCEDURE sp{i} AS SELECT * FROM Table{i}"
        
        test_cases.append(sql)
    
    analyzer = CodeQualityAnalyzer()
    start = time.time()
    
    results = []
    for sql in test_cases:
        result = analyzer.analyze(sql, f'sp{len(results)}')
        results.append(result)
    
    elapsed = time.time() - start
    
    assert len(results) == 50
    assert elapsed < 5.0,  f"Batch analysis took {elapsed}s (should be < 5s)"
    print(f"✅ Analyzed 50 SPs in {elapsed:.3f}s")

# Additional hardcore edge cases

def test_schema_qualified_everything():
    """Test 22: Everything fully schema-qualified."""
    sql = """
    CREATE PROCEDURE [Production].[usp_GetData]
        @Id [INT] = NULL
AS
    BEGIN
        SELECT [t1].[Col1], [t2].[Col2]
        FROM [dbo].[Table1] AS [t1]
        INNER JOIN [dbo].[Table2] AS [t2] ON [t1].[Id] = [t2].[Id]
        WHERE [t1].[Id] = @Id
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'Production' in result['name'] or 'usp_GetData' in result['name']
    print("✅ Parsed fully schema-qualified SQL")

def test_inline_table_valued_function():
    """Test 23: Inline TVF parsing."""
    sql = """
    CREATE FUNCTION dbo.fn_GetOrders(@CustomerId INT)
    RETURNS TABLE
    AS
    RETURN
    (
        SELECT OrderId, OrderDate, TotalAmount
        FROM Orders
        WHERE CustomerId = @CustomerId
    )
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert 'Orders' in result['tables']
    print("✅ Parsed inline table-valued function")

def test_security_complete_report():
    """Test 24: Complete security report generation."""
    dangerous_sql = """
    CREATE PROCEDURE dbo.VulnerableSP AS
    EXEC xp_cmdshell 'dir'
    EXEC('SELECT * FROM Users WHERE Name = ''' + @Input + '''')
    -- password: admin123
    EXECUTE AS USER = 'sa'
    """
    
    analyzer = SecurityAnalyzer()
    result = analyzer.analyze(dangerous_sql)
    
    # Should find all vulnerabilities
    assert len(result['sql_injection_risks']) > 0
    assert len(result['permission_issues']) > 0
    assert len(result['security_warnings']) > 0
    
    score = analyzer.get_security_score(dangerous_sql)
    assert score < 50, f"Dangerous SQL scored {score} (should be < 50)"
    
    print(f"✅ Detected all security issues, score: {score}/100")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 HARDCORE TEST SUITE - WORLD-CLASS VALIDATION")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
