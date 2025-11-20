import pytest
from src.parser.sp_parser import SPParser
from src.analyzer.dependency_resolver import DependencyResolver

@pytest.fixture
def parser():
    return SPParser()

@pytest.fixture
def resolver():
    return DependencyResolver()

def test_resolve_tables(parser, resolver):
    sql = """
    CREATE PROCEDURE dbo.TestTables
    AS
    BEGIN
        SELECT * FROM dbo.Users u
        JOIN Sales.Orders o ON u.Id = o.UserId
        WHERE u.Active = 1
    END
    """
    ast = parser.parse(sql)
    deps = resolver.get_dependencies(ast)
    assert "dbo.Users" in deps['tables']
    assert "Sales.Orders" in deps['tables']

def test_resolve_exec(parser, resolver):
    sql = """
    CREATE PROCEDURE dbo.TestExec
    AS
    BEGIN
        EXEC dbo.SubProc;
        EXECUTE dbo.AnotherProc @p=1;
    END
    """
    ast = parser.parse(sql)
    deps = resolver.get_dependencies(ast)
    assert "dbo.SubProc" in deps['procedures']
    assert "dbo.AnotherProc" in deps['procedures']
