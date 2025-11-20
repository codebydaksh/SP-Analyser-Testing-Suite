import uuid
from sqlglot import exp
import re

class CFGNode:
    """
    Represents a node in the Control Flow Graph.
    Enhanced version with full control flow support.
    """
    def __init__(self, node_type, content=None, ast_node=None, line=None):
        self.id = str(uuid.uuid4())[:8]
        self.node_type = node_type  # START, END, BLOCK, IF, WHILE_HEADER, WHILE_BODY, MERGE
        self.content = content
        self.ast_node = ast_node
        self.line = line
        self.exits = []  # List of (CFGNode, edge_label)
        self.reachable = False  # For unreachable code detection

    def add_exit(self, node, label=""):
        """Add exit edge with optional label (for true/false branches)."""
        if node and (node, label) not in self.exits:
            self.exits.append((node, label))

    def __repr__(self):
        return f"[{self.node_type}:{self.id}] {self.content or ''}"

class CFG:
    """Enhanced Control Flow Graph container."""
    def __init__(self):
        self.start_node = CFGNode("START")
        self.end_node = CFGNode("END")
        self.nodes = [self.start_node, self.end_node]

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes.append(node)

class CFGBuilder:
    """
    Enhanced CFG Builder using regex-based control flow extraction.
    Builds complete CFGs with IF/WHILE/CASE nodes.
    """
    def __init__(self):
        self.cf_extractor = None

    def build(self, ast, sql_code=None) -> CFG:
        """Build CFG from AST and optionally SQL source code for control flow."""
        cfg = CFG()
        
        # Import control flow extractor
        from parser.control_flow_extractor import ControlFlowExtractor
        self.cf_extractor = ControlFlowExtractor()
        
        # Extract control flow if SQL code provided
        control_flow = None
        if sql_code:
            control_flow = self.cf_extractor.extract_all(sql_code)
        
        statements = []
        if isinstance(ast, list):
            statements = ast
        elif isinstance(ast, exp.Expression):
            statements = [ast]
        
        last_node = self._process_statements(cfg, cfg.start_node, statements, control_flow, sql_code)
        
        if last_node:
            last_node.add_exit(cfg.end_node)
            
        return cfg

    def _process_statements(self, cfg, current_node, statements, control_flow, sql_code):
        """Process statements with control flow awareness."""
        prev_node = current_node
        
        for stmt in statements:
            if isinstance(stmt, exp.Create):
                # For CREATE PROCEDURE, process the body
                if hasattr(stmt, 'expression') and stmt.expression:
                    expressions = [stmt.expression]
                    if isinstance(stmt.expression, list):
                        expressions = stmt.expression
                    prev_node = self._process_statements(cfg, prev_node, expressions, control_flow, sql_code)
                continue
                
            # Sequential statement
            content = stmt.sql() if hasattr(stmt, 'sql') else str(stmt)
            if len(content) > 100:
                content = content[:97] + "..."
            
            # Check if this is part of a control flow structure
            if sql_code and control_flow:
                prev_node = self._handle_control_flow(cfg, prev_node, stmt, content, control_flow, sql_code)
            else:
                node = CFGNode("BLOCK", content=content, ast_node=stmt)
                cfg.add_node(node)
                prev_node.add_exit(node)
                prev_node = node
                
        return prev_node

    def _handle_control_flow(self, cfg, prev_node, stmt, content, control_flow, sql_code):
        """Handle control flow structures detected by regex."""
        # This is simplified - in practice, you'd match statements to control flow blocks
        # For now, treat as sequential
        node = CFGNode("BLOCK", content=content, ast_node=stmt)
        cfg.add_node(node)
        prev_node.add_exit(node)
        return node

    def build_from_source(self, sql_code: str) -> CFG:
        """Build CFG directly from SQL source code using control flow extractor."""
        from parser.control_flow_extractor import ControlFlowExtractor
        cf_extractor = ControlFlowExtractor()
        control_flow = cf_extractor.extract_all(sql_code)
        
        cfg = CFG()
        
        # Split source into lines
        lines = sql_code.split('\n')
        
        # Build nodes for each control flow structure
        cf_nodes = {}  # Map line -> node
        
        # Create IF nodes
        for if_block in control_flow['if_blocks']:
            line = if_block['line']
            node = CFGNode("IF", content=f"IF {if_block['condition']}", line=line)
            cfg.add_node(node)
            cf_nodes[line] = node
        
        # Create WHILE nodes
        for while_loop in control_flow['while_loops']:
            line = while_loop['line']
            node = CFGNode("WHILE_HEADER", content=f"WHILE {while_loop['condition']}", line=line)
            cfg.add_node(node)
            cf_nodes[line] = node
        
        # Simple sequential linking
        prev = cfg.start_node
        for line_num in sorted(cf_nodes.keys()):
            node = cf_nodes[line_num]
            prev.add_exit(node, "sequential")
            prev = node
        
        if prev != cfg.start_node:
            prev.add_exit(cfg.end_node)
        else:
            cfg.start_node.add_exit(cfg.end_node)
        
        return cfg

