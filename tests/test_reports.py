import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from reports.html_generator import HTMLReportGenerator
from reports.markdown_generator import MarkdownReportGenerator
from reports.csv_generator import CSVSummaryGenerator

def test_html_report_generation():
    """Test HTML report generation."""
    analysis_data = {
        'sp_name': 'dbo.TestProc',
        'basic': {'lines_of_code': 50},
        'security': {'score': 95, 'sql_injection_risks': [], 'permission_issues': []},
        'quality': {'grade': 'A', 'quality_score': 92, 'issues': []},
        'performance': {'performance_score': 88, 'issues': []},
        'complexity': {'complexity': 2, 'code_blocks': 3, 'if_statements': 1, 'while_loops': 0},
        'dependencies': {'tables': ['Users', 'Orders'], 'procedures': []}
    }
    
    generator = HTMLReportGenerator()
    html = generator.generate(analysis_data, 'dbo.TestProc')
    
    assert '<!DOCTYPE html>' in html
    assert 'dbo.TestProc' in html
    assert '95' in html  # Security score
    assert 'A' in html   # Quality grade

def test_markdown_report_generation():
    """Test Markdown report generation."""
    analysis_data = {
        'sp_name': 'dbo.TestProc',
        'basic': {'lines_of_code': 50},
        'security': {'score': 95, 'sql_injection_risks': [], 'permission_issues': []},
        'quality': {'grade': 'A', 'quality_score': 92, 'issues': []},
        'performance': {'performance_score': 88, 'issues': []},
        'complexity': {'complexity': 2, 'code_blocks': 3, 'if_statements': 1, 'while_loops': 0},
        'dependencies': {'tables': ['Users'], 'procedures': []}
    }
    
    generator = MarkdownReportGenerator()
    md = generator.generate(analysis_data, 'dbo.TestProc')
    
    assert '# Analysis Report' in md
    assert 'dbo.TestProc' in md
    assert '95/100' in md
    assert '## ' in md  # Has sections

def test_csv_summary_generation(tmp_path):
    """Test CSV batch summary generation."""
    results = [
        {
            'sp_name': 'sp1',
            'source': 'file1.sql',
            'basic': {'lines_of_code': 100},
            'security': {'score': 90, 'sql_injection_risks': [], 'permission_issues': []},
            'quality': {'grade': 'A', 'quality_score': 88, 'issues': []},
            'performance': {'performance_score': 85, 'issues': []},
            'complexity': {'complexity': 3},
            'dependencies': {'tables': ['T1', 'T2'], 'procedures': ['sp2']}
        },
        {
            'sp_name': 'sp2',
            'source': 'file2.sql',
            'basic': {'lines_of_code': 50},
            'security': {'score': 95, 'sql_injection_risks': [], 'permission_issues': []},
            'quality': {'grade': 'B', 'quality_score': 82, 'issues': [{}]},
            'performance': {'performance_score': 90, 'issues': []},
            'complexity': {'complexity': 1},
            'dependencies': {'tables': ['T1'], 'procedures': []}
        }
    ]
    
    csv_file = tmp_path / "summary.csv"
    generator = CSVSummaryGenerator()
    generator.generate(results, str(csv_file))
    
    assert csv_file.exists()
    content = csv_file.read_text()
    assert 'Procedure Name' in content
    assert 'sp1' in content
    assert 'sp2' in content

def test_html_with_security_issues():
    """Test HTML report with security issues."""
    analysis_data = {
        'sp_name': 'dbo.Vulnerable',
        'basic': {'lines_of_code': 30},
        'security': {
            'score': 60,
            'sql_injection_risks': [
                {'type': 'Dynamic SQL', 'severity': 'HIGH', 'message': 'Test', 'recommendation': 'Fix it'}
            ],
            'permission_issues': []
        },
        'quality': {'grade': 'C', 'quality_score': 70, 'issues': []},
        'performance': {'performance_score': 80, 'issues': []},
        'complexity': {'complexity': 1, 'code_blocks': 1, 'if_statements': 0, 'while_loops': 0},
        'dependencies': {'tables': [], 'procedures': []}
    }
    
    generator = HTMLReportGenerator()
    html = generator.generate(analysis_data, 'dbo.Vulnerable')
    
    assert 'Dynamic SQL' in html
    assert 'HIGH' in html

def test_markdown_with_performance_issues():
    """Test Markdown report with performance issues."""
    analysis_data = {
        'sp_name': 'dbo.Slow',
        'basic': {'lines_of_code': 40},
        'security': {'score': 95, 'sql_injection_risks': [], 'permission_issues': []},
        'quality': {'grade': 'B', 'quality_score': 85, 'issues': []},
        'performance': {
            'performance_score': 65,
            'issues': [
                {'issue': 'Cursor Usage', 'severity': 'HIGH', 'impact': 'Slow', 'recommendation': 'Use SET-based', 'example': 'code'}
            ]
        },
        'complexity': {'complexity': 2, 'code_blocks': 2, 'if_statements': 0, 'while_loops': 1},
        'dependencies': {'tables': ['Orders'], 'procedures': []}
    }
    
    generator = MarkdownReportGenerator()
    md = generator.generate(analysis_data, 'dbo.Slow')
    
    assert 'Cursor Usage' in md
    assert 'Performance' in md
