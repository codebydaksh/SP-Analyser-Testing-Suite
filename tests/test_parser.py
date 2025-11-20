import pytest
from src.parser.sp_parser import SPParser
from sqlglot import exp

def test_parser_valid_sql():
    parser = SPParser()
    sql = "CREATE PROCEDURE dbo.Test AS SELECT 1"
    ast = parser.parse(sql)
    assert ast is not None
    assert isinstance(ast, exp.Create)

def test_parser_invalid_sql():
    parser = SPParser()
    sql = "CREATE PROCEDURE dbo.Test AS SELECT * FROM" # Invalid
    with pytest.raises(ValueError):
        parser.parse(sql)
