"""
Execution Path Analyzer for Control Flow Graphs
"""
from typing import List, Set
from analyzer.cfg_builder import CFG, CFGNode

class PathAnalyzer:
    """Analyzes execution paths through a CFG."""
    
    def __init__(self):
        pass
    
    def get_all_paths(self, cfg: CFG) -> List[List[CFGNode]]:
        """
        Get all possible execution paths from START to END.
        Uses DFS to enumerate paths.
        """
        paths = []
        current_path = []
        visited = set()
        
        self._dfs_paths(cfg.start_node, cfg.end_node, current_path, paths, visited)
        
        return paths
    
    def _dfs_paths(self, current: CFGNode, target: CFGNode, path: List[CFGNode], 
                   all_paths: List[List[CFGNode]], visited: Set[str]):
        """DFS to find all paths."""
        path.append(current)
        visited.add(current.id)
        
        if current == target:
            all_paths.append(path.copy())
        else:
            for exit_node, _ in current.exits:
                if exit_node.id not in visited:
                    self._dfs_paths(exit_node, target, path, all_paths, visited)
        
        path.pop()
        visited.remove(current.id)
    
    def detect_unreachable(self, cfg: CFG) -> List[CFGNode]:
        """
        Detect unreachable code blocks.
        Returns list of nodes not reachable from START.
        """
        # Mark all nodes as unreachable
        for node in cfg.nodes:
            node.reachable = False
        
        # DFS from START to mark reachable nodes
        self._mark_reachable(cfg.start_node)
        
        # Return unreachable nodes (excluding END)
        unreachable = [n for n in cfg.nodes if not n.reachable and n != cfg.end_node]
        
        return unreachable
    
    def _mark_reachable(self, node: CFGNode):
        """Mark node and descendants as reachable."""
        if node.reachable:
            return
        
        node.reachable = True
        for exit_node, _ in node.exits:
            self._mark_reachable(exit_node)
    
    def detect_infinite_loops(self, cfg: CFG) -> List[CFGNode]:
        """
        Detect potential infinite loops.
        Returns list of WHILE_HEADER nodes that may loop infinitely.
        """
        infinite_loops = []
        
        for node in cfg.nodes:
            if node.node_type == "WHILE_HEADER":
                # Check if loop has exit condition
                # Simple heuristic: loop is infinite if condition is constant true (1=1, TRUE, etc.)
                if node.content and self._is_constant_true(node.content):
                    infinite_loops.append(node)
        
        return infinite_loops
    
    def _is_constant_true(self, condition: str) -> bool:
        """Check if condition is always true."""
        condition_upper = condition.upper().strip()
        
        # Common constant true patterns
        constant_patterns = [
            '1=1', '1 = 1',
            'TRUE',
            '\'TRUE\'',
            '1<2', '1 < 2',
        ]
        
        for pattern in constant_patterns:
            if pattern in condition_upper:
                return True
        
        return False
