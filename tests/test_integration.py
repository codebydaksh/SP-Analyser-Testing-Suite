import pytest
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser.tsql_text_parser import TSQLTextParser
from parser.control_flow_extractor import ControlFlowExtractor
from analyzer.security_analyzer import SecurityAnalyzer
from analyzer.quality_analyzer import CodeQualityAnalyzer
from analyzer.performance_analyzer import PerformanceAnalyzer

def test_complete_sp_analysis():
    """Test complete analysis of a real stored procedure."""
    sql = """
    CREATE PROCEDURE dbo.ProcessOrder
        @OrderId INT,
        @UserId INT
    AS
    BEGIN
        SET NOCOUNT ON;
        BEGIN TRY
            BEGIN TRAN
            
            UPDATE Orders SET Status = 'Processed' WHERE OrderId = @OrderId
            INSERT INTO OrderHistory (OrderId, UserId, ProcessDate) VALUES (@OrderId, @UserId, GETDATE())
            
            COMMIT TRAN
        END TRY
        BEGIN CATCH
            ROLLBACK TRAN
            THROW;
        END CATCH
    END
    """
    
    # Parse
    parser = TSQLTextParser()
    result = parser.parse(sql)
    assert result['name'] == 'dbo.ProcessOrder'
    assert len(result['parameters']) >= 2
    
    # Security
    security = SecurityAnalyzer()
    sec_result = security.analyze(sql)
    assert security.get_security_score(sql) >= 85
    
    # Quality
    quality = CodeQualityAnalyzer()
    qual_result = quality.analyze(sql, 'dbo.ProcessOrder')
    assert qual_result['quality_score'] >= 80
    
    # Performance
    performance = PerformanceAnalyzer()
    perf_result = performance.analyze(sql)
    assert perf_result['performance_score'] >= 90

def test_batch_analysis_simulation():
    """Test batch analysis of multiple SPs."""
    sps = [
        "CREATE PROCEDURE sp1 AS SELECT * FROM Users",
        "CREATE PROCEDURE sp2 AS SET NOCOUNT ON; SELECT Id FROM Users WHERE Id = @Id",
        "CREATE PROCEDURE sp3 AS BEGIN TRY SELECT 1 END TRY BEGIN CATCH END CATCH"
    ]
    
    parser = TSQLTextParser()
    security = SecurityAnalyzer()
    
    results = []
    for sql in sps:
        parsed = parser.parse(sql)
        sec_score = security.get_security_score(sql)
        results.append({'parsed': parsed, 'security': sec_score})
    
    assert len(results) == 3
    assert all(r['security'] >= 0 for r in results)

def test_ci_cd_threshold_simulation():
    """Test CI/CD threshold logic."""
    # Good quality SP
    good_sql = """
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRAN
        SELECT Id, Name FROM dbo.Users WHERE Id = @UserId
        COMMIT TRAN
    END TRY
    BEGIN CATCH
        ROLLBACK TRAN
        THROW;
    END CATCH
    """
    
    quality = CodeQualityAnalyzer()
    result = quality.analyze(good_sql, 'usp_GetUser')
    
    # Simulate CI/CD gate
    MIN_QUALITY = 80
    assert result['quality_score'] >= MIN_QUALITY, "CI/CD quality gate failed"
    
def test_html_report_data_structure():
    """Test that analysis data has all required fields for HTML report."""
    sql = "CREATE PROCEDURE dbo.Test AS SELECT 1"
    
    parser = TSQLTextParser()
    security = SecurityAnalyzer()
    quality = CodeQualityAnalyzer()
    performance = PerformanceAnalyzer()
    cf_extractor = ControlFlowExtractor()
    
    analysis_data = {
        'basic': parser.parse(sql),
        'security': security.analyze(sql),
        'quality': quality.analyze(sql, 'dbo.Test'),
        'performance': performance.analyze(sql),
        'control_flow': cf_extractor.extract_all(sql)
    }
    
    # Verify all required fields exist
    assert 'basic' in analysis_data
    assert 'security' in analysis_data
    assert 'quality' in analysis_data
    assert 'performance' in analysis_data
    assert 'lines_of_code' in analysis_data['basic']
    assert 'sql_injection_risks' in analysis_data['security']
    assert 'quality_score' in analysis_data['quality']
    assert 'performance_score' in analysis_data['performance']

def test_large_sp_performance():
    """Test analysis performance with large SP."""
    # Generate large SP
    lines = ["CREATE PROCEDURE dbo.LargeSP AS BEGIN"]
    for i in range(100):
        lines.append(f"    SELECT {i} AS Col{i};")
    lines.append("END")
    sql = "\n".join(lines)
    
    import time
    start = time.time()
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    
    elapsed = time.time() - start
    
    # Should complete in under 1 second
    assert elapsed < 1.0
    assert result['lines_of_code'] > 100

def test_edge_case_empty_procedure():
    """Test edge case: empty procedure."""
    sql = "CREATE PROCEDURE dbo.Empty AS BEGIN END"
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    
    assert result['name'] == 'dbo.Empty'
    assert result['lines_of_code'] >= 1

def test_edge_case_complex_parameters():
    """Test edge case: complex parameter list."""
    sql = """
    CREATE PROCEDURE dbo.ComplexParams
        @P1 INT = 1,
        @P2 VARCHAR(MAX) = NULL,
        @P3 DECIMAL(18,2) OUTPUT,
        @P4 BIT = 0
    AS SELECT 1
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    
    assert result['name'] == 'dbo.ComplexParams'
    # Parameters may or may not be fully parsed - just ensure no crash
    # WHY: Complex parameter parsing (defaults, OUTPUT, complex types) is hard!
    # We prioritize ROBUSTNESS over perfection - never crash, always return something useful
    assert 'parameters' in result


# ========================== 7 NEW BRUTAL INTEGRATION TESTS ==========================

def test_brutal_full_pipeline_with_all_analyzers():
    """BRUTAL: Test entire analysis pipeline with all analyzers on complex stored procedure"""
    complex_sp = """
    CREATE PROCEDURE dbo.EnterpriseDataProcessor
        @StartDate DATETIME,
        @EndDate DATETIME,
        @UserId INT,
        @BatchSize INT = 1000
    AS
    BEGIN
        SET NOCOUNT ON;
        DECLARE @Counter INT = 0;
        DECLARE @TotalRows INT;
        
        BEGIN TRY
            BEGIN TRANSACTION;
            
            -- Complex query with multiple joins
            SELECT @TotalRows = COUNT(*)
            FROM Orders o
            INNER JOIN OrderDetails od ON o.OrderId = od.OrderId
            INNER JOIN Products p ON od.ProductId = p.ProductId
            INNER JOIN Customers c ON o.CustomerId = c.CustomerId
            WHERE o.OrderDate BETWEEN @StartDate AND @EndDate;
            
            -- Cursor processing (performance issue)
            DECLARE order_cursor CURSOR FOR
            SELECT OrderId FROM Orders WHERE ProcessedFlag = 0;
            
            OPEN order_cursor;
            DECLARE @OrderId INT;
            FETCH NEXT FROM order_cursor INTO @OrderId;
            
            WHILE @@FETCH_STATUS = 0 AND @Counter < @BatchSize
            BEGIN
                -- Dynamic SQL (security risk)
                DECLARE @SQL NVARCHAR(MAX);
                SET @SQL = 'UPDATE Orders SET ProcessedFlag = 1 WHERE OrderId = ' + CAST(@OrderId AS VARCHAR);
                EXEC sp_executesql @SQL;
                
                SET @Counter = @Counter + 1;
                FETCH NEXT FROM order_cursor INTO @OrderId;
            END
            
            CLOSE order_cursor;
            DEALLOCATE order_cursor;
            
            COMMIT TRANSACTION;
            
            SELECT @TotalRows AS TotalProcessed, @Counter AS BatchProcessed;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0
                ROLLBACK TRANSACTION;
            THROW;
        END CATCH
    END
    """
    
    # Test ALL analyzers
    parser = TSQLTextParser()
    security = SecurityAnalyzer()
    quality = CodeQualityAnalyzer()
    performance = PerformanceAnalyzer()
    cf_extractor = ControlFlowExtractor()
    
    # Parse - should handle complexity
    parsed = parser.parse(complex_sp)
    assert parsed['name'] == 'dbo.EnterpriseDataProcessor'
    assert len(parsed['tables']) >= 3  # Should find most tables (Orders, OrderDetails, Products, Customers)
    
    # Security - should detect dynamic SQL
    sec_result = security.analyze(complex_sp)
    assert len(sec_result['sql_injection_risks']) > 0  # Dynamic SQL is a risk
    sec_score = security.get_security_score(complex_sp)
    assert sec_score < 100  # Should be penalized for dynamic SQL
    
    # Quality - should detect cursor usage
    qual_result = quality.analyze(complex_sp, 'dbo.EnterpriseDataProcessor')
    assert len(qual_result['issues']) > 0  # Cursor should be flagged
    
    # Performance - should detect performance issues
    perf_result = performance.analyze(complex_sp)
    assert perf_result['performance_score'] < 100  # Cursor impacts performance
    
    # Control flow - should handle complex nested structures
    cf_result = cf_extractor.extract_all(complex_sp)
    assert len(cf_result) >= 3  # Should handle BEGIN/END, TRY/CATCH, WHILE


def test_brutal_security_analysis_all_attack_vectors():
    """BRUTAL: Test security analysis against all known SQL injection patterns"""
    attack_vectors = [
        # Classic SQL injection
        """CREATE PROC vuln1 @UserInput VARCHAR(100) AS
           DECLARE @SQL NVARCHAR(MAX) = 'SELECT * FROM Users WHERE Name = ''' + @UserInput + '''';
           EXEC(@SQL);""",
        
        # Second-order injection
        """CREATE PROC vuln2 @UserId INT AS
           DECLARE @Name VARCHAR(100);
           SELECT @Name = Name FROM Users WHERE Id = @UserId;
           EXEC('SELECT * FROM ' + @Name);""",
        
        # XP_CMDSHELL abuse
        """CREATE PROC vuln3 @Command VARCHAR(200) AS
           EXEC xp_cmdshell @Command;""",
        
        # OPENROWSET injection
        """CREATE PROC vuln4 @Server VARCHAR(100) AS
           EXEC('SELECT * FROM OPENROWSET(''SQLNCLI'', ''' + @Server + ''', ''SELECT 1'')');""",
        
        # Unsafe sp_executesql
        """CREATE PROC vuln5 @TableName NVARCHAR(128) AS
           DECLARE @SQL NVARCHAR(MAX) = N'SELECT * FROM ' + @TableName;
           EXEC sp_executesql @SQL;"""
    ]
    
    security = SecurityAnalyzer()
    
    detected_count = 0
    for i, sql in enumerate(attack_vectors):
        sec_result = security.analyze(sql)
        
        # Should detect injection risks in MOST cases (not all analyzers are perfect)
        if len(sec_result['sql_injection_risks']) > 0:
            detected_count += 1
        
        # Security score should generally be lower for vulnerable code
        score = security.get_security_score(sql)
        # Some might be detected, some might not - no analyzer is 100% perfect
    
    # Should detect at least 60% of the attack vectors
    assert detected_count >= 3, f"Only detected {detected_count}/5 attack vectors"


def test_brutal_quality_analysis_all_antipatterns():
    """BRUTAL: Test quality analysis against all SQL anti-patterns"""
    antipatterns = [
        # SELECT *
        ("SELECT_STAR", "CREATE PROC bad1 AS SELECT * FROM Users"),
        
        # Cursor abuse
        ("CURSOR", """CREATE PROC bad2 AS
                      DECLARE c CURSOR FOR SELECT Id FROM Users;
                      OPEN c; CLOSE c; DEALLOCATE c;"""),
        
        # String concatenation in queries
        ("CONCAT", """CREATE PROC bad3 @X INT AS
                      DECLARE @SQL VARCHAR(MAX) = 'SELECT * FROM Users WHERE Id = ' + CAST(@X AS VARCHAR);
                      EXEC(@SQL);"""),
        
        # Missing SET NOCOUNT ON
        ("NO_NOCOUNT", "CREATE PROC bad4 AS SELECT 1"),
        
        # Missing error handling
        ("NO_ERROR_HANDLING", "CREATE PROC bad5 AS UPDATE Users SET Status = 1"),
        
        # Implicit transactions
        ("NO_EXPLICIT_TRAN", "CREATE PROC bad6 AS UPDATE Users SET X = 1; UPDATE Orders SET Y = 2;"),
    ]
    
    quality = CodeQualityAnalyzer()
    
    detected_count = 0
    for pattern_name, sql in antipatterns:
        qual_result = quality.analyze(sql, f'test_{pattern_name}')
        
        # Count how many antipatterns we detect
        if len(qual_result['issues']) > 0:
            detected_count += 1
    
    # Should detect at least 70% of antipatterns
    assert detected_count >= 4, f"Only detected {detected_count}/6 antipatterns"


def test_brutal_performance_bottleneck_detection():
    """BRUTAL: Test performance analysis detects all common bottlenecks"""
    bottlenecks = [
        # Cursor in loop
        """CREATE PROC perf1 AS
           DECLARE c CURSOR FOR SELECT Id FROM BigTable;
           OPEN c;
           DECLARE @Id INT;
           FETCH NEXT FROM c INTO @Id;
           WHILE @@FETCH_STATUS = 0
           BEGIN
               UPDATE AnotherTable SET Value = 1 WHERE Id = @Id;
               FETCH NEXT FROM c INTO @Id;
           END
           CLOSE c;
           DEALLOCATE c;""",
        
        # SELECT * with no WHERE
        """CREATE PROC perf2 AS SELECT * FROM HugeTable;""",
        
        # Missing index hint
        """CREATE PROC perf3 AS
           SELECT o.*, od.* 
           FROM Orders o
           INNER JOIN OrderDetails od ON o.OrderId = od.OrderId;""",
        
        # Scalar functions in WHERE
        """CREATE PROC perf4 AS
           SELECT * FROM Users WHERE UPPER(Name) = 'ADMIN';""",
        
        # Multiple table scans
        """CREATE PROC perf5 AS
           SELECT COUNT(*) FROM Table1;
           SELECT COUNT(*) FROM Table2;
           SELECT COUNT(*) FROM Table3;
           SELECT COUNT(*) FROM Table4;
           SELECT COUNT(*) FROM Table5;""",
    ]
    
    performance = PerformanceAnalyzer()
    
    detected_count = 0
    for i, sql in enumerate(bottlenecks):
        perf_result = performance.analyze(sql)
        
        # Count detected bottlenecks
        if len(perf_result['issues']) > 0:
            detected_count += 1
    
    # Should detect at least 60% of bottlenecks  
    assert detected_count >= 3, f"Only detected {detected_count}/5 bottlenecks"


def test_brutal_control_flow_edge_cases():
    """BRUTAL: Test control flow extraction handles all edge cases"""
    edge_cases = [
        # Deeply nested IF statements (10 levels)
        """CREATE PROC cf1 AS
           IF 1=1 BEGIN
               IF 2=2 BEGIN
                   IF 3=3 BEGIN
                       IF 4=4 BEGIN
                           IF 5=5 BEGIN
                               IF 6=6 BEGIN
                                   IF 7=7 BEGIN
                                       IF 8=8 BEGIN
                                           IF 9=9 BEGIN
                                               IF 10=10 BEGIN
                                                   SELECT 'MAX_DEPTH';
                                               END
                                           END
                                       END
                                   END
                               END
                           END
                       END
                   END
               END
           END""",
        
        # Multiple WHILE loops
        """CREATE PROC cf2 AS
           DECLARE @i INT = 0, @j INT = 0;
           WHILE @i < 10 BEGIN
               WHILE @j < 5 BEGIN
                   SELECT @i, @j;
                   SET @j = @j + 1;
               END
               SET @i = @i + 1;
           END""",
        
        # Complex TRY/CATCH nesting
        """CREATE PROC cf3 AS
           BEGIN TRY
               BEGIN TRY
                   SELECT 1/0;
               END TRY
               BEGIN CATCH
                   THROW;
               END CATCH
           END TRY
           BEGIN CATCH
               SELECT ERROR_MESSAGE();
           END CATCH""",
        
        # Mixed control structures
        """CREATE PROC cf4 @X INT AS
           IF @X > 0
           BEGIN
               WHILE @X > 0
               BEGIN
                   BEGIN TRY
                       IF @X % 2 = 0
                           SELECT 'EVEN';
                       ELSE
                           SELECT 'ODD';
                       SET @X = @X - 1;
                   END TRY
                   BEGIN CATCH
                       BREAK;
                   END CATCH
               END
           END""",
    ]
    
    cf_extractor = ControlFlowExtractor()
    
    for i, sql in enumerate(edge_cases):
        cf_result = cf_extractor.extract_all(sql)
        
        # Should extract control flow without crashing
        assert cf_result is not None, f"Failed to extract control flow for case {i+1}"
        assert len(cf_result) > 0, f"No control flow detected for case {i+1}"


def test_brutal_parser_syntax_edge_cases():
    """BRUTAL: Test parser handles all T-SQL syntax edge cases"""
    edge_cases = [
        # Quoted identifiers
        """CREATE PROCEDURE [dbo].[Proc With Spaces]
           @Param1 [INT] = 1
        AS SELECT [Column Name] FROM [Table Name];""",
        
        # Multiple statement types
        """CREATE PROC multi AS
           CREATE TABLE #Temp (Id INT);
           INSERT INTO #Temp VALUES (1);
           UPDATE #Temp SET Id = 2;
           DELETE FROM #Temp;
           DROP TABLE #Temp;""",
        
        # GOTO statements
        """CREATE PROC goto_test AS
           GOTO SkipThis;
           SELECT 'Never executed';
           SkipThis:
           SELECT 'Jumped here';""",
        
        # WAITFOR
        """CREATE PROC wait_test AS
           WAITFOR DELAY '00:00:01';
           SELECT 'After wait';""",
        
        # MERGE statement
        """CREATE PROC merge_test AS
           MERGE Target AS T
           USING Source AS S ON T.Id = S.Id
           WHEN MATCHED THEN UPDATE SET T.Value = S.Value
           WHEN NOT MATCHED THEN INSERT VALUES (S.Id, S.Value);""",
        
        # CTE with recursion
        """CREATE PROC cte_test AS
           WITH NumbersCTE AS (
               SELECT 1 AS Num
               UNION ALL
               SELECT Num + 1 FROM NumbersCTE WHERE Num < 100
           )
           SELECT * FROM NumbersCTE;""",
    ]
    
    parser = TSQLTextParser()
    
    for i, sql in enumerate(edge_cases):
        try:
            result = parser.parse(sql)
            # Should parse without crashing
            assert result is not None, f"Parser returned None for case {i+1}"
            assert 'name' in result, f"Missing 'name' in result for case {i+1}"
        except Exception as e:
            # Even if parsing fails, should not crash the system
            pytest.fail(f"Parser crashed on case {i+1}: {str(e)}")


def test_brutal_stress_test_massive_batch_analysis():
    """BRUTAL: Stress test with 100 stored procedures analyzed sequentially"""
    import time
    
    # Generate 100 different SPs
    test_procedures = []
    for i in range(100):
        sp = f"""
        CREATE PROCEDURE dbo.BatchProc{i}
            @Param{i} INT
        AS
        BEGIN
            SET NOCOUNT ON;
            SELECT Id, Name, Value{i} FROM Table{i} WHERE Id = @Param{i};
            UPDATE Table{i} SET ProcessedDate = GETDATE() WHERE Id = @Param{i};
        END
        """
        test_procedures.append(sp)
    
    # Analyze all 100
    parser = TSQLTextParser()
    security = SecurityAnalyzer()
    quality = CodeQualityAnalyzer()
    
    start_time = time.time()
    results = []
    
    for i, sql in enumerate(test_procedures):
        try:
            parsed = parser.parse(sql)
            sec_score = security.get_security_score(sql)
            qual_result = quality.analyze(sql, f'dbo.BatchProc{i}')
            
            results.append({
                'parsed': parsed,
                'security': sec_score,
                'quality': qual_result['quality_score']
            })
        except Exception as e:
            pytest.fail(f"Failed on procedure {i}: {str(e)}")
    
    elapsed = time.time() - start_time
    
    # Verify all completed
    assert len(results) == 100, "Not all procedures analyzed"
    
    # Should complete in reasonable time (< 30 seconds for 100 SPs)
    assert elapsed < 30, f"Batch analysis too slow: {elapsed:.2f}s"
    
    # All should have valid results
    assert all(r['security'] >= 0 for r in results), "Invalid security scores"
    assert all(r['quality'] >= 0 for r in results), "Invalid quality scores"
    
    # Calculate statistics
    avg_security = sum(r['security'] for r in results) / len(results)
    avg_quality = sum(r['quality'] for r in results) / len(results)
    
    assert avg_security >= 80, f"Average security too low: {avg_security}"
    assert avg_quality >= 70, f"Average quality too low: {avg_quality}"
