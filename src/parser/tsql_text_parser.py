"""
Robust T-SQL Text Parser
Works without sqlglot limitations - parses raw SQL text
"""
import re
from typing import Dict, List, Any

class TSQLTextParser:
    """Parse T-SQL stored procedures from raw text."""
    
    def __init__(self):
        self.proc_name_pattern = re.compile(r'CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+(\[?[\w.]+\]?)', re.IGNORECASE)
        self.table_pattern = re.compile(r'\b(?:FROM|JOIN|INTO|UPDATE)\s+(\[?[\w.]+\]?)', re.IGNORECASE)
        self.exec_pattern = re.compile(r'\bEXEC(?:UTE)?\s+(\[?[\w.]+\]?)', re.IGNORECASE)
        
    def parse(self, sql_text: str) -> Dict[str, Any]:
        """Parse SP and return structured data."""
        return {
            'name': self.extract_proc_name(sql_text),
            'parameters': self.extract_parameters(sql_text),
            'tables': self.extract_tables(sql_text),
            'exec_calls': self.extract_exec_calls(sql_text),
            'lines_of_code': self.count_lines_of_code(sql_text),
            'has_try_catch': 'BEGIN TRY' in sql_text.upper(),
            'has_transaction': 'BEGIN TRAN' in sql_text.upper(),
        }
    
    def extract_proc_name(self, sql_text: str) -> str:
        """Extract procedure name."""
        match = self.proc_name_pattern.search(sql_text)
        if match:
            name = match.group(1).strip('[]')
            return name
        return 'Unknown'
    
    def extract_parameters(self, sql_text: str) -> List[Dict[str, str]]:
        """Extract parameters from CREATE PROCEDURE statement."""
        parameters = []
        
        # Enhanced pattern to capture parameters with types and defaults
        # FIXED: Handles multiple params separated by commas
        param_pattern = r'@(\w+)\s+([\w\(\),\s]+?)(?:\s*=\s*([^,]+))?(?=\s*,|\s*$)'
        
        # Find parameters in the signature
        create_match = re.search(r'CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+[\[\].\w]+\s*(.*?)\s+AS\b', 
                                sql_text, re.IGNORECASE | re.DOTALL)
        
        if create_match:
            params_section = create_match.group(1)
            for match in re.finditer(param_pattern, params_section):
                param_name = '@' + match.group(1)
                param_type = match.group(2).strip()
                default_value = match.group(3).strip() if match.group(3) else None
                
                parameters.append({
                    'name': param_name,
                    'type': param_type,
                    'default': default_value
                })
        
        return parameters
    
    def extract_tables(self, sql_text: str) -> List[str]:
        """Extract table names including temp tables and CTEs."""
        tables = set()
        
        # Pattern 1: FROM/JOIN/INTO/UPDATE clauses
        for match in self.table_pattern.finditer(sql_text):
            table = match.group(1).strip('[]')
            if not table.startswith('@'):  # Only exclude variables, INCLUDE temp tables
                # Normalize: remove schema prefix to avoid duplicates (e.g., 'dbo.Sales' -> 'Sales')
                if '.' in table:
                    table = table.split('.', 1)[1]
                tables.add(table)
        
        # Pattern 2: CREATE TABLE #TempTable and ##GlobalTemp
        create_table_pattern = re.compile(r'CREATE\s+TABLE\s+(##?\w+)', re.IGNORECASE)
        for match in create_table_pattern.finditer(sql_text):
            temp_table = match.group(1)
            tables.add(temp_table)
        
        # Pattern 3: CTEs (Common Table Expressions) - WITH SomeCTE AS (...)
        cte_pattern = re.compile(r'WITH\s+(\w+)\s+AS\s*\(', re.IGNORECASE)
        for match in cte_pattern.finditer(sql_text):
            cte_name = match.group(1)
            tables.add(cte_name)
        
        return sorted(list(tables))
    
    def extract_exec_calls(self, sql_text: str) -> List[str]:
        """Extract EXEC procedure calls."""
        procs = set()
        for match in self.exec_pattern.finditer(sql_text):
            proc = match.group(1).strip('[]')
            if not proc.startswith('@'):  # Exclude variable execution
                procs.add(proc)
        return sorted(list(procs))
    
    def count_lines_of_code(self, sql_text: str) -> int:
        """Count non-empty, non-comment lines."""
        lines = sql_text.split('\n')
        code_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('--'):
                code_lines += 1
        return code_lines
