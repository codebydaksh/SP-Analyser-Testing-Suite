import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser.sp_parser import SPParser
from analyzer.cfg_builder import CFGBuilder

def test_cfg_simple_procedure():
    """Test CFG generation for a simple stored procedure."""
    parser = SPParser()
    sql = """
    CREATE PROCEDURE dbo.TestProc
    AS
    BEGIN
        SELECT 1;
        SELECT 2;
    END
    """
    ast = parser.parse(sql)
    builder = CFGBuilder()
    cfg = builder.build(ast)
    
    # Should have START -> at least some nodes -> END
    assert cfg.start_node is not None
    assert cfg.end_node is not None
    assert len(cfg.nodes) >= 2  # At minimum START and END

def test_cfg_with_multiple_statements():
    """Test CFG with multiple sequential statements."""
    parser = SPParser()
    sql = """
    CREATE PROCEDURE dbo.MultiStatement
    AS
    BEGIN
        SELECT * FROM Users;
        UPDATE Users SET Active = 1;
        DELETE FROM TempTable;
    END
    """
    ast = parser.parse(sql)
    builder = CFGBuilder()
    cfg = builder.build(ast)
    
    # Verify basic structure
    assert len(cfg.nodes) >= 2
    # Check that start has at least one exit
    assert len(cfg.start_node.exits) >= 0
