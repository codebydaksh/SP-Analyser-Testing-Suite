"""
Comprehensive tests for LogicExplainer - World-class coverage
NEW FILE - Testing before replacing existing
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from analyzer.logic_explainer import LogicExplainer
from analyzer.cfg_builder import CFG, CFGNode


class TestLogicExplainerComprehensive:
    """Comprehensive test suite for logic explainer - 95%+ coverage target"""
    
    def test_init(self):
        """Test LogicExplainer initialization"""
        explainer = LogicExplainer()
        assert explainer is not None
    
    # ========== explain_path tests ==========
    
    def test_explain_path_empty_list(self):
        """Test empty path returns appropriate message"""
        explainer = LogicExplainer()
        result = explainer.explain_path([])
        assert result == "Empty path"
    
    def test_explain_path_start_node(self):
        """Test START node explanation"""
        explainer = LogicExplainer()
        node = CFGNode(node_type="START", content="BEGIN")
        result = explainer.explain_path([node])
        assert "starts execution" in result.lower()
    
    def test_explain_path_end_node(self):
        """Test END node explanation"""
        explainer = LogicExplainer()
        node = CFGNode(node_type="END", content="END")
        result = explainer.explain_path([node])
        assert "completes" in result.lower()
    
    def test_explain_path_if_node(self):
        """Test IF node with condition"""
        explainer = LogicExplainer()
        node = CFGNode(node_type="IF", content="@Status > 0")
        result = explainer.explain_path([node])
        assert "If the condition" in result
        assert "@Status > 0" in result
    
    def test_explain_path_while_node(self):
        """Test WHILE_HEADER node"""
        explainer = LogicExplainer()
        node = CFGNode(node_type="WHILE_HEADER", content="@Counter < 100")
        result = explainer.explain_path([node])
        assert "While the condition" in result
        assert "@Counter < 100" in result
    
    def test_explain_path_block_node_short(self):
        """Test BLOCK node with short content"""
        explainer = LogicExplainer()
        node = CFGNode(node_type="BLOCK", content="SELECT * FROM Users")
        result = explainer.explain_path([node])
        assert "Execute:" in result
        assert "SELECT * FROM Users" in result
    
    def test_explain_path_block_node_long_truncation(self):
        """Test BLOCK node content truncation for long SQL"""
        explainer = LogicExplainer()
        long_sql = "SELECT * FROM Users WHERE UserId > 1000 AND Status = 'Active' AND Department IS NOT NULL"
        node = CFGNode(node_type="BLOCK", content=long_sql)
        result = explainer.explain_path([node])
        # Content longer than 60 chars should be truncated
        if len(long_sql) >= 60:
            assert "..." in result
    
    def test_explain_path_merge_node(self):
        """Test MERGE node"""
        explainer = LogicExplainer()
        node = CFGNode(node_type="MERGE", content="")
        result = explainer.explain_path([node])
        assert "Then continue with:" in result
    
    def test_explain_path_multiple_nodes_numbered(self):
        """Test path with multiple nodes produces numbered list"""
        explainer = LogicExplainer()
        path = [
            CFGNode(node_type="START", content=""),
            CFGNode(node_type="BLOCK", content="DECLARE @X INT"),
            CFGNode(node_type="IF", content="@X > 0"),
            CFGNode(node_type="END", content="")
        ]
        result = explainer.explain_path(path)
        # Check for numbered output
        assert "1." in result
    def test_summarize_simple_linear_cfg(self):
        """Test summary of simple linear flow"""
        explainer = LogicExplainer()
        cfg = CFG()
        
        cfg.add_node(CFGNode(node_type="START", content=""))
        cfg.add_node(CFGNode(node_type="BLOCK", content="SELECT 1"))
        cfg.add_node(CFGNode(node_type="END", content=""))
        
        result = explainer.summarize_control_flow(cfg)
        
        # CFG.add_node() adds START/END automatically, so we get 5 nodes total
        assert result['total_nodes'] >= 3
        assert result['if_statements'] == 0
        assert result['while_loops'] == 0
        assert result['code_blocks'] == 1
        assert result['complexity'] == 0  # No control flow
    
    def test_summarize_cfg_with_if_statements(self):
        """Test summary counts IF statements correctly"""
        explainer = LogicExplainer()
        cfg = CFG()
        
        cfg.add_node(CFGNode(node_type="START", content=""))
        cfg.add_node(CFGNode(node_type="IF", content="@X > 0"))
        cfg.add_node(CFGNode(node_type="IF", content="@Y < 10"))
        cfg.add_node(CFGNode(node_type="END", content=""))
        
        result = explainer.summarize_control_flow(cfg)
        
        assert result['if_statements'] == 2
        assert result['complexity'] == 2  # 2 IFs
        assert result['total_nodes'] >= 2
    
    def test_summarize_cfg_with_while_loops(self):
        """Test summary counts WHILE loops correctly"""
        explainer = LogicExplainer()
        cfg = CFG()
        
        cfg.add_node(CFGNode(node_type="START", content=""))
        cfg.add_node(CFGNode(node_type="WHILE_HEADER", content="@I < 100"))
        cfg.add_node(CFGNode(node_type="WHILE_HEADER", content="@J != 0"))
        cfg.add_node(CFGNode(node_type="END", content=""))
        
        result = explainer.summarize_control_flow(cfg)
        
        assert result['while_loops'] == 2
        assert result['complexity'] == 2  # 2 WHILEs
        assert result['total_nodes'] >= 2
    
    def test_summarize_cfg_complex_mixed(self):
        """Test summary with mixed control structures"""
        explainer = LogicExplainer()
        cfg = CFG()
        
        # Add nodes (note: cfg.add_node() also creates START/END automatically)
        node1 = CFGNode(node_type="IF", content="")
        node2 = CFGNode(node_type="BLOCK", content="")
        node3 = CFGNode(node_type="WHILE_HEADER", content="")
        node4 = CFGNode(node_type="BLOCK", content="")
        node5 = CFGNode(node_type="IF", content="")
        node6 = CFGNode(node_type="BLOCK", content="")
        node7 = CFGNode(node_type="WHILE_HEADER", content="")
        node8 = CFGNode(node_type="IF", content="")
        node9 = CFGNode(node_type="BLOCK", content="")
        
        cfg.add_node(node1)
        cfg.add_node(node2)
        cfg.add_node(node3)
        cfg.add_node(node4)
        cfg.add_node(node5)
        cfg.add_node(node6)
        cfg.add_node(node7)
        cfg.add_node(node8)
        cfg.add_node(node9)
        
        result = explainer.summarize_control_flow(cfg)
        
        # Verify counts (exact number may vary based on CFG.add_node implementation)
        assert result['if_statements'] == 3
        assert result['while_loops'] == 2
        assert result['code_blocks'] == 4
        assert result['complexity'] == 5  # 3 IFs + 2 WHILEs
        assert result['total_nodes'] >= 9  # At least the nodes we added
    
    def test_summarize_return_dict_structure(self):
        """Test summary returns correct dictionary keys"""
        explainer = LogicExplainer()
        cfg = CFG()
        result = explainer.summarize_control_flow(cfg)
        
        assert 'total_nodes' in result
        assert 'if_statements' in result
        assert 'while_loops' in result
        assert 'code_blocks' in result
        assert 'complexity' in result
        assert len(result) == 5  # Exactly 5 keys
