import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyzer.quality_analyzer import CodeQualityAnalyzer

def test_naming_convention_good():
    """Test proper SP naming convention."""
    analyzer = CodeQualityAnalyzer()
    sql = "SELECT * FROM Users"
    result = analyzer.analyze(sql, "usp_GetUsers")
    issues = [i for i in result['issues'] if i['category'] == 'Naming']
    assert len(issues) == 0

def test_naming_convention_bad():
    """Test improper SP naming convention."""
    analyzer = CodeQualityAnalyzer()
    sql = "SELECT * FROM Users"
    result = analyzer.analyze(sql, "GetUsers")
    issues = [i for i in result['issues'] if i['category'] == 'Naming']
    assert len(issues) > 0

def test_select_star_detection():
    """Test SELECT * detection."""
    analyzer = CodeQualityAnalyzer()
    sql = "SELECT * FROM Users"
    result = analyzer.analyze(sql, "usp_Test")
    issues = [i for i in result['issues'] if 'SELECT *' in i['message']]
    assert len(issues) > 0

def test_update_without_where():
    """Test UPDATE without WHERE clause."""
    analyzer = CodeQualityAnalyzer()
    sql = "UPDATE Users SET Active = 1"
    result = analyzer.analyze(sql, "usp_Test")
    issues = [i for i in result['issues'] if i['severity'] == 'HIGH']
    assert len(issues) > 0

def test_delete_without_where():
    """Test DELETE without WHERE clause."""
    analyzer = CodeQualityAnalyzer()
    sql = "DELETE FROM Users"
    result = analyzer.analyze(sql, "usp_Test")
    issues = [i for i in result['issues'] if 'DELETE' in i['message']]
    assert len(issues) > 0

def test_nolock_overuse():
    """Test NOLOCK hint overuse."""
    analyzer = CodeQualityAnalyzer()
    sql = """
    SELECT * FROM T1 WITH(NOLOCK)
    JOIN T2 WITH(NOLOCK) ON T1.Id = T2.Id
    JOIN T3 WITH(NOLOCK) ON T2.Id = T3.Id
    JOIN T4 WITH(NOLOCK) ON T3.Id = T4.Id
    """
    result = analyzer.analyze(sql, "usp_Test")
    issues = [i for i in result['issues'] if'NOLOCK' in i['message']]
    assert len(issues) > 0

def test_set_nocount_missing():
    """Test missing SET NOCOUNT ON."""
    analyzer = CodeQualityAnalyzer()
    sql = "SELECT * FROM Users"
    result = analyzer.analyze(sql, "usp_Test")
    issues = [i for i in result['issues'] if 'NOCOUNT' in i['message']]
    assert len(issues) > 0

def test_set_nocount_present():
    """Test SET NOCOUNT ON present."""
    analyzer = CodeQualityAnalyzer()
    sql = "SET NOCOUNT ON; SELECT * FROM Users"
    result = analyzer.analyze(sql, "usp_Test")
    assert result['quality_score'] > 50

def test_quality_score_excellent():
    """Test excellent code quality."""
    analyzer = CodeQualityAnalyzer()
    sql = """
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRAN
        SELECT Col1, Col2 FROM dbo.Users WHERE Id = @Id
        COMMIT TRAN
    END TRY
    BEGIN CATCH
        ROLLBACK TRAN
        THROW;
    END CATCH
    """
    result = analyzer.analyze(sql, "usp_GetUser")
    assert result['quality_score'] >= 90
    assert result['grade'] in ['A', 'B']

def test_quality_score_poor():
    """Test poor code quality."""
    analyzer = CodeQualityAnalyzer()
    sql = "SELECT * FROM Users; UPDATE Users SET Active = 1"
    result = analyzer.analyze(sql, "GetUsers")
    assert result['quality_score'] < 70

def test_grade_a():
    """Test A grade."""
    analyzer = CodeQualityAnalyzer()
    assert analyzer.get_grade(95) == 'A'

def test_grade_b():
    """Test B grade."""
    analyzer = CodeQualityAnalyzer()
    assert analyzer.get_grade(85) == 'B'

def test_grade_c():
    """Test C grade."""
    analyzer = CodeQualityAnalyzer()
    assert analyzer.get_grade(75) == 'C'

def test_grade_f():
    """Test F grade."""
    analyzer = CodeQualityAnalyzer()
    assert analyzer.get_grade(50) == 'F'
