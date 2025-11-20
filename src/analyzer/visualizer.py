"""
Graphviz Visualization Generator for CFGs
"""
from analyzer.cfg_builder import CFG

class Visualizer:
    """Generate Graphviz DOT format for CFG visualization."""
    
    def __init__(self):
        pass
    
    def generate_dot(self, cfg: CFG) -> str:
        """
        Generate Graphviz DOT format string for the CFG.
        Can be rendered with: dot -Tpng cfg.dot -o cfg.png
        """
        lines = []
        lines.append("digraph CFG {")
        lines.append("    rankdir=TB;")  # Top to bottom layout
        lines.append("    node [shape=box, style=rounded];")
        lines.append("")
        
        # Add nodes with styling
        for node in cfg.nodes:
            label = self._escape_label(node.content or node.node_type)
            shape, style = self._get_node_style(node.node_type)
            
            lines.append(f'    "{node.id}" [label="{label}", shape={shape}, style="{style}"];')
        
        lines.append("")
        
        # Add edges
        for node in cfg.nodes:
            for exit_node, edge_label in node.exits:
                label_attr = f' [label="{edge_label}"]' if edge_label else ''
                lines.append(f'    "{node.id}" -> "{exit_node.id}"{label_attr};')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _escape_label(self, text: str) -> str:
        """Escape special characters for DOT format."""
        return text.replace('"', '\\"').replace('\n', '\\n')
    
    def _get_node_style(self, node_type: str) -> tuple:
        """Get shape and style for node type."""
        styles = {
            "START": ("ellipse", "filled,bold", "#90EE90"),  # Light green
            "END": ("ellipse", "filled,bold", "#FFB6C1"),    # Light pink
            "IF": ("diamond", "filled", "#87CEEB"),          # Sky blue
            "WHILE_HEADER": ("hexagon", "filled", "#DDA0DD"), # Plum
            "BLOCK": ("box", "rounded", "#FFFACD"),          # Lemon chiffon
            "MERGE": ("point", "filled", "#D3D3D3"),         # Light gray
        }
        
        if node_type in styles:
            shape, style, color = styles[node_type]
            return shape, f"{style},fillcolor=\"{color}\""
        
        return "box", "rounded"
    
    def save_dot(self, cfg: CFG, filename: str):
        """Save CFG as DOT file."""
        dot_content = self.generate_dot(cfg)
        with open(filename, 'w') as f:
            f.write(dot_content)
        print(f"CFG saved to: {filename}")
        print(f"To render: dot -Tpng {filename} -o {filename.replace('.dot', '.png')}")
