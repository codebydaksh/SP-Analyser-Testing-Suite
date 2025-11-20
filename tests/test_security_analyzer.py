import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyzer.security_analyzer import SecurityAnalyzer

def test_sql_injection_dynamic_sql():
    """Test SQL injection detection with dynamic SQL."""
    analyzer = SecurityAnalyzer()
    sql = "EXEC(@sql)"
    result = analyzer.analyze(sql)
    assert len(result['sql_injection_risks']) > 0
    assert result['sql_injection_risks'][0]['severity'] == 'HIGH'

def test_sql_injection_concatenation():
    """Test SQL injection detection with string concatenation."""
    analyzer = SecurityAnalyzer()
    sql = "SELECT * FROM Users WHERE Name = '" + " + @UserName + " + "'"
    result = analyzer.analyze(sql)
    assert len(result['sql_injection_risks']) > 0

def test_permission_xp_procedures():
    """Test detection of extended procedures."""
    analyzer = SecurityAnalyzer()
    sql = "EXEC xp_cmdshell 'dir'"
    result = analyzer.analyze(sql)
    assert len(result['permission_issues']) > 0
    assert 'xp_' in result['permission_issues'][0]['message'].lower()

def test_permission_execute_as():
    """Test detection of EXECUTE AS."""
    analyzer = SecurityAnalyzer()
    sql = "EXECUTE AS USER = 'admin'"
    result = analyzer.analyze(sql)
    assert len(result['permission_issues']) > 0

def test_security_warnings_no_try_catch():
    """Test warning for missing TRY-CATCH."""
    analyzer = SecurityAnalyzer()
    sql = "SELECT * FROM Users"
    result = analyzer.analyze(sql)
    warnings = result['security_warnings']
    assert any('TRY-CATCH' in w['message'] for w in warnings)

def test_security_warnings_sensitive_data():
    """Test detection of sensitive data in comments."""
    analyzer = SecurityAnalyzer()
    sql = "-- password: secret123"
    result = analyzer.analyze(sql)
    warnings = result['security_warnings']
    assert any('sensitive' in w['message'].lower() for w in warnings)

def test_security_score_perfect():
    """Test security score with perfect code."""
    analyzer = SecurityAnalyzer()
    sql = """
    BEGIN TRY
        SELECT * FROM Users WHERE Id = @UserId
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
    """
    score = analyzer.get_security_score(sql)
    assert score >= 95

def test_security_score_issues():
    """Test security score with multiple issues."""
    analyzer = SecurityAnalyzer()
    sql = "EXEC(@sql + @input); EXEC xp_cmdshell 'dir'"
    score = analyzer.get_security_score(sql)
    assert score < 70

def test_no_issues():
    """Test clean SQL with no security issues."""
    analyzer = SecurityAnalyzer()
    sql = """
    BEGIN TRY
        SELECT Col1, Col2 FROM dbo.Table1 WHERE Id = @Id
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
    """
    result = analyzer.analyze(sql)
    assert len(result['sql_injection_risks']) == 0
    assert len(result['permission_issues']) == 0
