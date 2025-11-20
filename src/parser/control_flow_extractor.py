"""
Control Flow Extractor for T-SQL Stored Procedures
Uses regex patterns to detect IF/WHILE/CASE structures
"""
import re
from typing import List, Dict, Any

class ControlFlowExtractor:
    """Extract control flow structures from T-SQL code."""
    
    def __init__(self):
        # Regex patterns for control flow
        self.if_pattern = re.compile(r'\bIF\s+(.+?)\s+BEGIN', re.IGNORECASE | re.DOTALL)
        self.while_pattern = re.compile(r'\bWHILE\s+(.+?)\s+BEGIN', re.IGNORECASE | re.DOTALL)
        self.case_pattern = re.compile(r'\bCASE\s+(.+?)\s+END', re.IGNORECASE | re.DOTALL)
    
    def extract_if_blocks(self, sql_code: str) -> List[Dict[str, Any]]:
        """Extract IF blocks with conditions."""
        blocks = []
        matches = self.if_pattern.finditer(sql_code)
        
        for match in matches:
            condition = match.group(1).strip()
            start_pos = match.start()
            
            # Find line number
            line_num = sql_code[:start_pos].count('\n') + 1
            
            blocks.append({
                'type': 'IF',
                'condition': condition,
                'line': line_num,
                'position': start_pos
            })
        
        return blocks
    
    def extract_while_loops(self, sql_code: str) -> List[Dict[str, Any]]:
        """Extract WHILE loops with conditions."""
        loops = []
        matches = self.while_pattern.finditer(sql_code)
        
        for match in matches:
            condition = match.group(1).strip()
            start_pos = match.start()
            line_num = sql_code[:start_pos].count('\n') + 1
            
            loops.append({
                'type': 'WHILE',
                'condition': condition,
                'line': line_num,
                'position': start_pos
            })
        
        return loops
    
    def extract_case_statements(self, sql_code: str) -> List[Dict[str, Any]]:
        """Extract CASE statements."""
        cases = []
        matches = self.case_pattern.finditer(sql_code)
        
        for match in matches:
            content = match.group(1).strip()
            start_pos = match.start()
            line_num = sql_code[:start_pos].count('\n') + 1
            
            cases.append({
                'type': 'CASE',
                'content': content,
                'line': line_num,
                'position': start_pos
            })
        
        return cases
    
    def extract_all(self, sql_code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all control flow structures."""
        return {
            'if_blocks': self.extract_if_blocks(sql_code),
            'while_loops': self.extract_while_loops(sql_code),
            'case_statements': self.extract_case_statements(sql_code)
        }
