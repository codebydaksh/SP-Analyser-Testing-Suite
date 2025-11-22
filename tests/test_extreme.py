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
from parser.control_flow_extractor import ControlFlowExtractor

# ===== EXTREME PRODUCTION TESTS =====

def test_real_world_2000_line_monster():
    """EXTREME 1: Real-world 2000-line enterprise SP."""
    sql_parts = [
        "CREATE PROCEDURE dbo.EnterpriseDataWarehouse",
        "    @StartDate DATETIME,",
        "    @EndDate DATETIME,",
        "    @Region VARCHAR(50) = NULL,",
        "    @ProductCategory VARCHAR(100) = NULL,",
        "    @IncludeArchived BIT = 0",
        "AS",
        "BEGIN",
        "    SET NOCOUNT ON;",
        "    SET XACT_ABORT ON;",
        "    ",
        "    DECLARE @ErrorMessage NVARCHAR(4000);",
        "    DECLARE @BatchCount INT = 0;",
        "    DECLARE @TotalProcessed BIGINT = 0;",
        ""
    ]
    
    # Generate ultra-complex business logic
    for i in range(400):
        sql_parts.extend([
            f"    -- Business rule {i + 1}",
            "    BEGIN TRY",
            "        BEGIN TRAN",
            f"        ",
            f"        IF @Region IS NOT NULL AND @Region = 'APAC'",
            "        BEGIN",
            f"            WITH SalesCTE AS (",
            f"                SELECT OrderID, SUM(Amount) as Total",
            f"                FROM Sales_{i % 10}",
            "                WHERE OrderDate >= @StartDate AND OrderDate < @EndDate",
            f"                GROUP BY OrderID",
            "            )",
            f"            UPDATE dbo.OrderSummary_{i % 5}",
            "            SET TotalSales = s.Total,",
            "                ProcessedDate = GETUTCDATE(),",
            f"                ProcessedBy = SUSER_SNAME()",
            f"            FROM dbo.OrderSummary_{i % 5} os",
            "            INNER JOIN SalesCTE s ON os.OrderID = s.OrderID",
            "            WHERE os.Status = 'Pending'",
            "        END",
            "        ELSE",
            "        BEGIN",
            f"            INSERT INTO dbo.RegionalStats_{i % 3} (Region, Sales, Date)",
            f"            SELECT @Region, SUM(Amount), @StartDate",
            f"            FROM Sales_{i % 10}",
            "            WHERE OrderDate >= @StartDate",
            f"            GROUP BY OrderDate",
            "        END",
            "        ",
            "        COMMIT TRAN",
            "        SET @BatchCount += 1",
            "    END TRY",
            "    BEGIN CATCH",
            "        IF @@TRANCOUNT > 0 ROLLBACK TRAN",
            "        SET @ErrorMessage = ERROR_MESSAGE()",
            "        RAISERROR(@ErrorMessage, 16, 1)",
            "    END CATCH",
            ""
        ])
    
    sql_parts.extend([
        "    -- Final aggregation",
        "    SELECT @TotalProcessed = COUNT(*) FROM dbo.ProcessLog",
        "    RETURN @TotalProcessed",
        "END"
    ])
    
    sql = "\n".join(sql_parts)
    
    start = time.time()
    parser = TSQLTextParser()
    result = parser.parse(sql)
    elapsed = time.time() - start
    
    assert elapsed < 3.0, f"2000-line SP took {elapsed}s (should be < 3s)"
    assert result['lines_of_code'] > 1500
    assert len(result['tables']) > 20
    print(f" MONSTER: {result['lines_of_code']} LOC, {len(result['tables'])} tables in {elapsed:.3f}s")

def test_sql_injection_obfuscation_techniques():
    """EXTREME 2: Detect sophisticated obfuscation."""
    advanced_injections = [
        # Base64-like obfuscation
        "DECLARE @q NVARCHAR(MAX) = CHAR(83)+CHAR(69)+CHAR(76)+CHAR(69)+CHAR(67)+CHAR(84); EXEC(@q + @UserInput)",
        
        # Nested dynamic SQL
        "DECLARE @outer NVARCHAR(MAX) = 'EXEC(''SELECT * FROM Users WHERE Name = ''''' + @Input + ''''''')'; EXEC sp_executesql @outer",
        
        # Variable swapping
        "DECLARE @temp NVARCHAR(MAX) = @Dangerous; SET @Safe = @temp; EXEC(@Safe)",
        
        # String functions
        "EXEC(REPLACE('SELECT~*~FROM~Users~WHERE~Id=!','~',' ')  + CAST(@UserId AS VARCHAR))",
        
        # sp_executesql with parameters (safer but still risky if dynamic)
        "EXEC sp_executesql N'SELECT * FROM ' + @TableName + ' WHERE Id = @Id', N'@Id INT', @Id = @UserId"
    ]
    
    analyzer = SecurityAnalyzer()
    detected = 0
    
    for sql in advanced_injections:
        result = analyzer.analyze(sql)
        if len(result['sql_injection_risks']) > 0:
            detected += 1
    
    # Should detect at least 80% of obfuscation techniques
    assert detected >= 4, f"Only detected {detected}/5 advanced injections"
    print(f" Detected {detected}/5 sophisticated SQL injection obfuscations")

def test_concurrent_batch_stress():
    """EXTREME 3: Simulate 100 concurrent SP analyses."""
    test_sp = """
    CREATE PROCEDURE dbo.StressTest AS
    SET NOCOUNT ON;
    SELECT * FROM Users u JOIN Orders o ON u.Id = o.UserId
    WHERE u.Active = 1 AND o.Status = 'Pending'
    """
    
    parser = TSQLTextParser()
    security = SecurityAnalyzer()
    quality = CodeQualityAnalyzer()
    performance = PerformanceAnalyzer()
    
    start = time.time()
    
    # Simulate 100 concurrent analyses
    for i in range(100):
        p_result = parser.parse(test_sp)
        s_result = security.analyze(test_sp)
        q_result = quality.analyze(test_sp, 'dbo.StressTest')
        perf_result = performance.analyze(test_sp)
    
    elapsed = time.time() - start
    
    # Should complete 100 full analyses in under 10 seconds
    assert elapsed < 10.0, f"100 analyses took {elapsed}s (should be < 10s)"
    print(f" 100 full analyses completed in {elapsed:.3f}s ({elapsed/100*1000:.1f}ms per SP)")

def test_every_tsql_keyword():
    """EXTREME 4: SP using every major T-SQL keyword."""
    sql = """
    CREATE PROCEDURE dbo.KeywordTest AS
    BEGIN
        -- DDL
        CREATE TABLE #temp (id INT)
        ALTER TABLE #temp ADD name VARCHAR(50)
        DROP TABLE #temp
        
        -- DML
        SELECT * FROM Users
        INSERT INTO Log VALUES (1, 'test')
        UPDATE Users SET Active = 1
        DELETE FROM Log WHERE Id < 0
        MERGE INTO Target USING Source ON Target.Id = Source.Id
            WHEN MATCHED THEN UPDATE SET Val = Source.Val
            WHEN NOT MATCHED THEN INSERT VALUES (Source.Id, Source.Val);
        
        -- Control Flow
        IF 1 = 1 BEGIN SELECT 1 END ELSE BEGIN SELECT 0 END
        WHILE 1 = 1 BREAK
        CASE WHEN 1=1 THEN 'yes' ELSE 'no' END
        GOTO label1
        label1:
        RETURN 1
        
        -- Transactions
        BEGIN TRAN
        COMMIT TRAN
        ROLLBACK TRAN
        SAVE TRAN sp1
        
        -- Error Handling
        BEGIN TRY
            RAISERROR('test', 16, 1)
        END TRY
        BEGIN CATCH
            THROW
        END CATCH
        
        -- CTEs & Subqueries
        ;WITH CTE AS (SELECT 1 AS n)
        SELECT * FROM CTE
        
        -- Window Functions
        SELECT ROW_NUMBER() OVER (ORDER BY id) FROM Users
        
        -- Set Operations
        SELECT 1 UNION SELECT 2
        SELECT 1 INTERSECT SELECT 1
        SELECT 1 EXCEPT SELECT 2
        
        -- Functions
        SELECT CAST(1 AS VARCHAR)
        SELECT CONVERT(VARCHAR, GETDATE())
        SELECT COALESCE(NULL, 'default')
        SELECT ISNULL(NULL, 0)
        
        -- Special
        EXEC sp_executesql N'SELECT 1'
        WAITFOR DELAY '00:00:01'
        PRINT 'message'
        
        -- Cursors
        DECLARE cur CURSOR FOR SELECT * FROM Users
        OPEN cur
        FETCH NEXT FROM cur
        CLOSE cur
        DEALLOCATE cur
    END
    """
    
    parser = TSQLTextParser()
    result = parser.parse(sql)
    
    # Should parse without errors
    assert result is not None
    assert result['name'] == 'dbo.KeywordTest'
    print(" Parsed SP using 50+ T-SQL keywords")

def test_maximum_complexity_cfg():
    """EXTREME 5: Maximum complexity control flow."""
    # Generate SP with cyclomatic complexity of 50+
    conditions = []
    for i in range(25):
        conditions.append(f"    IF @Condition{i} = 1 BEGIN SELECT {i} END")
        conditions.append(f"    ELSE IF @Condition{i} = 2 BEGIN SELECT {i+100} END")
    
    sql = f"""
    CREATE PROCEDURE dbo.MaxComplexity AS
    BEGIN
        {chr(10).join(conditions)}
        
        WHILE @Counter < 100
        BEGIN
            IF @Flag = 1 OR @Flag = 2 OR @Flag = 3
                SELECT 'complex'
            SET @Counter += 1
        END
    END
    """
    
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql)
    
    from analyzer.logic_explainer import LogicExplainer
    explainer = LogicExplainer()
    complexity_result = explainer.summarize_control_flow(cfg)
    
    assert complexity_result['complexity'] > 20
    print(f" Built CFG with complexity: {complexity_result['complexity']}")

def test_all_security_vulnerabilities_at_once():
    """EXTREME 6: SP with EVERY security issue."""
    vulnerable_sp = """
    CREATE PROCEDURE dbo.VulnerableKitchenSink
        @UserInput VARCHAR(MAX),
        @Password VARCHAR(50)
    AS
    BEGIN
        -- SQL Injection
        DECLARE @sql NVARCHAR(MAX) = 'SELECT * FROM Users WHERE Name = ''' + @UserInput + ''''
        EXEC(@sql)
        
        -- xp_ procedures
        EXEC xp_cmdshell 'dir C:\\'
        EXEC xp_regread 'HKEY_LOCAL_MACHINE'
        
        -- EXECUTE AS
        EXECUTE AS USER = 'sa'
        SELECT * FROM sys.databases
        REVERT
        
        -- Sensitive data in comments
        -- username: admin
        -- password: P@ssw0rd123
        -- api_key: sk_live_abc123
        
        -- String concatenation
        SET @sql = 'DELETE FROM Users WHERE ' + @UserInput
        EXEC sp_executesql @sql
        
        -- No error handling
        UPDATE CriticalTable SET Value = @UserInput
        
        -- Hardcoded credentials
        DECLARE @conn VARCHAR(200) = 'Server=prod;User=sa;Password=pass123;'
    END
    """
    
    analyzer = SecurityAnalyzer()
    result = analyzer.analyze(vulnerable_sp)
    score = analyzer.get_security_score(vulnerable_sp)
    
    # Should find multiple issues and have very low score
    assert len(result['sql_injection_risks']) >= 2
    assert len(result['permission_issues']) >= 2
    assert len(result['security_warnings']) >= 2
    assert score < 30
    
    total_issues = (len(result['sql_injection_risks']) + 
                   len(result['permission_issues']) + 
                   len(result['security_warnings']))
    
    print(f" Detected {total_issues} security issues, score: {score}/100")

def test_performance_nightmare():
    """EXTREME 7: SP with ALL performance anti-patterns."""
    nightmare_sp = """
    CREATE PROCEDURE dbo.PerformanceNightmare AS
    BEGIN
        -- Cursors (worst)
        DECLARE c CURSOR FOR SELECT * FROM LargeTable
        OPEN c
        FETCH NEXT FROM c INTO @var
        WHILE @@FETCH_STATUS = 0
        BEGIN
            FETCH NEXT FROM c
        END
        CLOSE c
        DEALLOCATE c
        
        -- Implicit conversions
        SELECT * FROM Users WHERE UserId = '123'
        SELECT * FROM Orders WHERE OrderId = '456'
        
        -- Functions in WHERE
        SELECT * FROM Customers WHERE UPPER(Name) = 'JOHN'
        SELECT * FROM Products WHERE YEAR(CreatedDate) = 2024
        SELECT * FROM Sales WHERE LEN(ProductCode) > 5
        
        -- Multiple OR conditions
        WHERE Status = 'A' OR Status = 'B' OR Status = 'C' OR Status = 'D' 
           OR Status = 'E' OR Status = 'F' OR Status = 'G'
        
        -- Leading wildcards
        SELECT * FROM Inventory WHERE SKU LIKE '%ABC'
        SELECT * FROM Catalog WHERE Description LIKE '%widget%'
        
        -- SELECT *
        INSERT INTO Archive SELECT * FROM Production.Orders
        SELECT * INTO #temp FROM LargeTable
        
        -- NOLOCK overuse
        SELECT * FROM T1 WITH(NOLOCK)
        JOIN T2 WITH(NOLOCK) ON T1.Id = T2.Id
        JOIN T3 WITH(NOLOCK) ON T2.Id = T3.Id
        JOIN T4 WITH(NOLOCK) ON T3.Id = T4.Id
        JOIN T5 WITH(NOLOCK) ON T4.Id = T5.Id
    END
    """
    
    analyzer = PerformanceAnalyzer()
    result = analyzer.analyze(nightmare_sp)
    score = result['performance_score']
    
    # Should detect many issues and have low score
    assert len(result['issues']) >= 5
    assert score < 50
    
    print(f" Detected {len(result['issues'])} performance issues, score: {score}/100")

def test_quality_perfect_vs_terrible():
    """EXTREME 8: Compare perfect and terrible code quality."""
    perfect_sp = """
    CREATE PROCEDURE usp_GetUserData
        @UserId INT,
        @IncludeOrders BIT = 0
    AS
    BEGIN
        SET NOCOUNT ON;
        SET XACT_ABORT ON;
        
        BEGIN TRY
            BEGIN TRAN
            
            -- Get user data
            SELECT 
                u.UserId,
                u.UserName,
                u.Email,
                u.CreatedDate
            FROM dbo.Users u WITH(READCOMMITTED)
            WHERE u.UserId = @UserId
                AND u.IsActive = 1;
            
            -- Get orders if requested
            IF @IncludeOrders = 1
            BEGIN
                SELECT 
                    o.OrderId,
                    o.OrderDate,
                    o.TotalAmount
                FROM dbo.Orders o WITH(READCOMMITTED)
                WHERE o.UserId = @UserId
                    AND o.Status IN ('Pending', 'Completed')
                ORDER BY o.OrderDate DESC;
            END
            
            COMMIT TRAN;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0 ROLLBACK TRAN;
            
            DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
            RAISERROR(@ErrorMessage, 16, 1);
        END CATCH
    END
    """
    
    terrible_sp = """
    CREATE PROCEDURE GetData AS
    SELECT * FROM Users
    UPDATE Users SET Active = 1
    DELETE FROM Log
    """
    
    analyzer = CodeQualityAnalyzer()
    
    perfect_result = analyzer.analyze(perfect_sp, 'usp_GetUserData')
    terrible_result = analyzer.analyze(terrible_sp, 'GetData')
    
    assert perfect_result['quality_score'] >= 90
    assert perfect_result['grade'] in ['A', 'A+']
    assert terrible_result['quality_score'] < 50
    assert terrible_result['grade'] in ['D', 'F']
    
    print(f" Perfect: {perfect_result['grade']} ({perfect_result['quality_score']}), " +
          f"Terrible: {terrible_result['grade']} ({terrible_result['quality_score']})")

def test_all_report_formats_generation():
    """EXTREME 9: Generate all report formats from single analysis."""
    sql = """
    CREATE PROCEDURE dbo.ReportTest AS
    SET NOCOUNT ON;
    BEGIN TRY
        SELECT Id, Name FROM dbo.Users WHERE Active = 1
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
    """
    
    # Full analysis
    from parser.tsql_text_parser import TSQLTextParser
    from analyzer.security_analyzer import SecurityAnalyzer
    from analyzer.quality_analyzer import CodeQualityAnalyzer
    from analyzer.performance_analyzer import PerformanceAnalyzer
    from reports.html_generator import HTMLReportGenerator
    from reports.markdown_generator import MarkdownReportGenerator
    
    parser = TSQLTextParser()
    basic = parser.parse(sql)
    
    security_analyzer = SecurityAnalyzer()
    security = security_analyzer.analyze(sql)
    security['score'] = security_analyzer.get_security_score(sql)
    
    quality_analyzer = CodeQualityAnalyzer()
    quality = quality_analyzer.analyze(sql, 'dbo.ReportTest')
    
    perf_analyzer = PerformanceAnalyzer()
    performance = perf_analyzer.analyze(sql)
    
    analysis_data = {
        'sp_name': 'dbo.ReportTest',
        'basic': basic,
        'security': security,
        'quality': quality,
        'performance': performance,
        'complexity': {'complexity': 1, 'code_blocks': 1, 'if_statements': 0, 'while_loops': 0},
        'dependencies': {'tables': basic['tables'], 'procedures': basic['exec_calls']}
    }
    
    # Generate all formats
    html_gen = HTMLReportGenerator()
    html = html_gen.generate(analysis_data, 'dbo.ReportTest')
    
    md_gen = MarkdownReportGenerator()
    md = md_gen.generate(analysis_data, 'dbo.ReportTest')
    
    # Verify reports contain key data
    assert 'dbo.ReportTest' in html
    assert 'dbo.ReportTest' in md
    assert 'Security Score' in md or 'security' in md.lower()
    
    print(" Generated HTML and Markdown reports successfully")

def test_end_to_end_ci_cd_pipeline():
    """EXTREME 10: Complete CI/CD pipeline simulation."""
    # Simulate a PR with new SP
    new_sp = """
    CREATE PROCEDURE usp_ProcessPayment
        @OrderId INT,
        @Amount DECIMAL(18,2)
    AS
    BEGIN
        SET NOCOUNT ON;
        BEGIN TRY
            BEGIN TRAN
            
            UPDATE dbo.Orders
            SET Status = 'Paid',
                PaidAmount = @Amount,
                PaidDate = GETUTCDATE()
            WHERE OrderId = @OrderId;
            
            INSERT INTO dbo.PaymentLog (OrderId, Amount, ProcessedDate)
            VALUES (@OrderId, @Amount, GETUTCDATE());
            
            COMMIT TRAN;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0 ROLLBACK TRAN;
            THROW;
        END CATCH
    END
    """
    
    # Run full analysis pipeline
    parser = TSQLTextParser()
    security_analyzer = SecurityAnalyzer()
    quality_analyzer = CodeQualityAnalyzer()
    perf_analyzer = PerformanceAnalyzer()
    
    # Parse
    parsed = parser.parse(new_sp)
    
    # Security check
    sec_result = security_analyzer.analyze(new_sp)
    sec_score = security_analyzer.get_security_score(new_sp)
    
    # Quality check
    qual_result = quality_analyzer.analyze(new_sp, 'usp_ProcessPayment')
    
    # Performance check
    perf_result = perf_analyzer.analyze(new_sp)
    
    # CI/CD Gates
    MIN_SECURITY = 85
    MIN_QUALITY = 80
    MIN_PERFORMANCE = 75
    
    gates_passed = True
    reasons = []
    
    if sec_score < MIN_SECURITY:
        gates_passed = False
        reasons.append(f"Security: {sec_score} < {MIN_SECURITY}")
    
    if qual_result['quality_score'] < MIN_QUALITY:
        gates_passed = False
        reasons.append(f"Quality: {qual_result['quality_score']} < {MIN_QUALITY}")
    
    if perf_result['performance_score'] < MIN_PERFORMANCE:
        gates_passed = False
        reasons.append(f"Performance: {perf_result['performance_score']} < {MIN_PERFORMANCE}")
    
    # This SP should pass all gates
    assert gates_passed, f"CI/CD gates failed: {', '.join(reasons)}"
    
    print(f" CI/CD Pipeline PASSED - Security: {sec_score}, Quality: {qual_result['quality_score']}, Performance: {perf_result['performance_score']}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" EXTREME PRODUCTION VALIDATION SUITE ")
    print("="*70 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
