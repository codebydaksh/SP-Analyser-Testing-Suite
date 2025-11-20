import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser.sp_parser import SPParser
from analyzer.test_generator import SPTestGenerator

def test_extract_parameters():
    """Test parameter extraction from stored procedure."""
    parser = SPParser()
    sql = """
    CREATE PROCEDURE dbo.TestProc
    AS
    BEGIN
        SELECT 1;
    END
    """
    ast = parser.parse(sql)
    generator = SPTestGenerator()
    params = generator.extract_parameters(ast)
    assert isinstance(params, list)

def test_generate_tsqlt_tests():
    """Test tSQLt test generation."""
    generator = SPTestGenerator()
    params = [
        {'name': '@userId', 'type': 'INT', 'default': None},
        {'name': '@userName', 'type': 'VARCHAR(50)', 'default': "'guest'"}
    ]
    tests = generator.generate_tsqlt_tests('dbo.GetUser', params)
    assert 'tSQLt.NewTestClass' in tests
    assert 'test_BasicExecution' in tests
    assert 'EXEC dbo.GetUser' in tests

def test_generate_ssdt_tests():
    """Test SSDT test generation."""
    generator = SPTestGenerator()
    params = [{'name': '@userId', 'type': 'INT', 'default': None}]
    tests = generator.generate_ssdt_tests('dbo.GetUser', params)
    assert 'SSDT Test Suite' in tests
    assert 'EXEC' in tests
    assert 'dbo.GetUser' in tests
