import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyzer.cfg_builder import CFGBuilder
from analyzer.path_analyzer import PathAnalyzer
from analyzer.logic_explainer import LogicExplainer
from analyzer.visualizer import Visualizer

def test_path_analyzer():
    """Test path analyzer on a simple CFG."""
    sql = """
    CREATE PROCEDURE dbo.TestProc
    AS
    BEGIN
        SELECT 1;
        SELECT 2;
    END
    """
    
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql)
    
    analyzer = PathAnalyzer()
    paths = analyzer.get_all_paths(cfg)
    
    assert len(paths) >= 1
    assert paths[0][0] == cfg.start_node
    assert paths[0][-1] == cfg.end_node

def test_unreachable_detector():
    """Test unreachable code detection."""
    sql = "CREATE PROCEDURE dbo.Test AS SELECT 1"
    
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql)
    
    analyzer = PathAnalyzer()
    unreachable = analyzer.detect_unreachable(cfg)
    
    # Should have no unreachable nodes in simple sequential code
    assert len(unreachable) == 0

def test_logic_explainer():
    """Test plain English explanation."""
    sql = "CREATE PROCEDURE dbo.Test AS SELECT 1"
    
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql)
    
    explainer = LogicExplainer()
    summary = explainer.summarize_control_flow(cfg)
    
    assert 'total_nodes' in summary
    assert summary['total_nodes'] >= 2  # At least START and END

def test_visualizer():
    """Test DOT generation."""
    sql = "CREATE PROCEDURE dbo.Test AS SELECT 1"
    
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql)
    
    viz = Visualizer()
    dot = viz.generate_dot(cfg)
    
    assert 'digraph CFG' in dot
    assert cfg.start_node.id in dot
    assert cfg.end_node.id in dot
