import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyzer.performance_analyzer import PerformanceAnalyzer

def test_cursor_detection():
    """Test cursor usage detection."""
    analyzer = PerformanceAnalyzer()
    sql = "DECLARE cur CURSOR FOR SELECT * FROM Users"
    result = analyzer.analyze(sql)
    issues = [i for i in result['issues'] if 'Cursor' in i['issue']]
    assert len(issues) > 0
    assert issues[0]['severity'] == 'HIGH'

def test_implicit_conversion():
    """Test implicit conversion detection."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT * FROM Users WHERE UserId = 123"
    result = analyzer.analyze(sql)
    issues = [i for i in result['issues'] if 'Implicit' in i['issue']]
    assert len(issues) > 0

def test_scalar_function_in_where():
    """Test scalar function in WHERE clause."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT * FROM Users WHERE UPPER(Name) = 'JOHN'"
    result = analyzer.analyze(sql)
    issues = [i for i in result['issues'] if 'Function' in i['issue']]
    assert len(issues) > 0

def test_or_conditions():
    """Test multiple OR conditions."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT * FROM Users WHERE Col1 = 'A' OR Col1 = 'B' OR Col1 = 'C' OR Col1 = 'D' OR Col1 = 'E'"
    result = analyzer.analyze(sql)
    issues = [i for i in result['issues'] if 'OR' in i['issue']]
    assert len(issues) > 0

def test_leading_wildcard():
    """Test LIKE with leading wildcard."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT * FROM Users WHERE Name LIKE '%Smith'"
    result = analyzer.analyze(sql)
    issues = [i for i in result['issues'] if 'Wildcard' in i['issue']]
    assert len(issues) > 0

def test_select_into():
    """Test SELECT INTO usage."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT * INTO NewTable FROM Users"
    result = analyzer.analyze(sql)
    issues = [i for i in result['issues'] if 'SELECT INTO' in i['issue']]
    assert len(issues) > 0

def test_performance_score_perfect():
    """Test perfect performance score."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT Id, Name FROM dbo.Users WHERE Id = @Id"
    result = analyzer.analyze(sql)
    assert result['performance_score'] == 100

def test_performance_score_cursor():
    """Test performance score with cursor."""
    analyzer = PerformanceAnalyzer()
    sql = "DECLARE cur CURSOR FOR SELECT * FROM Users"
    result = analyzer.analyze(sql)
    assert result['performance_score'] <= 75

def test_performance_score_multiple_issues():
    """Test performance score with multiple issues."""
    analyzer = PerformanceAnalyzer()
    sql = """
    DECLARE cur CURSOR FOR SELECT * FROM Users WHERE Name LIKE '%Smith'
    SELECT * FROM Users WHERE UPPER(Name) = 'JOHN' OR UserId = 123
    """
    result = analyzer.analyze(sql)
    assert result['performance_score'] < 60

def test_no_performance_issues():
    """Test SQL with no performance issues."""
    analyzer = PerformanceAnalyzer()
    sql = "SELECT Id, Name, Email FROM dbo.Users WHERE Id = @UserId"
    result = analyzer.analyze(sql)
    assert len(result['issues']) == 0
    assert result['performance_score'] == 100
    assert result['grade'] == 'A'

def test_grade_calculation():
    """Test performance grade calculation."""
    analyzer = PerformanceAnalyzer()
    assert analyzer.get_grade(95) == 'A'
    assert analyzer.get_grade(85) == 'B'
    assert analyzer.get_grade(75) == 'C'
    assert analyzer.get_grade(65) == 'D'
    assert analyzer.get_grade(50) == 'F'

def test_example_recommendations():
    """Test that recommendations include examples."""
    analyzer = PerformanceAnalyzer()
    sql = "DECLARE cur CURSOR FOR SELECT * FROM Users"
    result = analyzer.analyze(sql)
    assert len(result['issues']) > 0
    assert 'example' in result['issues'][0]
    assert len(result['issues'][0]['example']) > 0
