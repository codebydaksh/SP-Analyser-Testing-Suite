"""
Plain English Logic Explainer for CFGs
"""
from typing import List
from analyzer.cfg_builder import CFGNode

class LogicExplainer:
    """Converts CFG paths to plain English explanations."""
    
    def __init__(self):
        pass
    
    def explain_path(self, path: List[CFGNode]) -> str:
        """
        Convert a path through the CFG to plain English.
        """
        if not path:
            return "Empty path"
        
        explanations = []
        
        for i, node in enumerate(path):
            if node.node_type == "START":
                explanations.append("The procedure starts execution.")
            elif node.node_type == "END":
                explanations.append("The procedure completes.")
            elif node.node_type == "IF":
                explanations.append(f"If the condition '{node.content}' is true:")
            elif node.node_type == "WHILE_HEADER":
                explanations.append(f"While the condition '{node.content}' is true, repeat:")
            elif node.node_type == "BLOCK":
                # Simplify block content for explanation
                content = node.content if len(node.content) < 60 else node.content[:57] + "..."
                explanations.append(f"Execute: {content}")
            elif node.node_type == "MERGE":
                explanations.append("Then continue with:")
        
        return "\n".join(f"{i+1}. {exp}" for i, exp in enumerate(explanations))
    
    def explain_cfg(self, cfg) -> str:
        """
        Explain the overall logic of the CFG.
        """
        from analyzer.path_analyzer import PathAnalyzer
        analyzer = PathAnalyzer()
        paths = analyzer.get_all_paths(cfg)
        
        if not paths:
            return "No execution paths found."
        
        explanation = [f"This stored procedure has {len(paths)} possible execution path(s):\n"]
        
        for i, path in enumerate(paths, 1):
            explanation.append(f"\n**Path {i}:**")
            explanation.append(self.explain_path(path))
        
        return "\n".join(explanation)
    
    def summarize_control_flow(self, cfg) -> dict:
        """
        Provide a summary of control flow complexity.
        """
        if_count = sum(1 for n in cfg.nodes if n.node_type == "IF")
        while_count = sum(1 for n in cfg.nodes if n.node_type == "WHILE_HEADER")
        block_count = sum(1 for n in cfg.nodes if n.node_type == "BLOCK")
        
        return {
            "total_nodes": len(cfg.nodes),
            "if_statements": if_count,
            "while_loops": while_count,
            "code_blocks": block_count,
            "complexity": if_count + while_count  # Simple cyclomatic complexity approximation
        }
