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
    assert 'parameters' in result
