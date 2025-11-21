"""
Performance Analyzer for T-SQL Stored Procedures
Detects performance anti-patterns and provides optimization recommendations
"""
import re
from typing import List, Dict

class PerformanceAnalyzer:
    """Analyze T-SQL for performance issues."""
    
    def analyze(self, sql_text: str) -> Dict:
        """Run all performance checks."""
        issues = []
        
        issues.extend(self.detect_cursor_usage(sql_text))
        issues.extend(self.detect_implicit_conversions(sql_text))
        issues.extend(self.detect_scalar_functions(sql_text))
        issues.extend(self.detect_or_conditions(sql_text))
        issues.extend(self.detect_leading_wildcards(sql_text))
        issues.extend(self.detect_select_into(sql_text))
        
        score = self.calculate_performance_score(issues)
        
        return {
            'issues': issues,
            'performance_score': score,
            'grade': self.get_grade(score)
        }
    
    def detect_cursor_usage(self, sql_text: str) -> List[Dict]:
        """Detect cursor usage (major performance issue)."""
        issues = []
        
        # Enhanced pattern to catch DECLARE CURSOR, OPEN, FETCH, etc.
        if re.search(r'\bDECLARE\s+\w+\s+CURSOR\s+FOR|DECLARE.*?CURSOR|OPEN\s+\w+|FETCH\s+(?:NEXT|PRIOR|FIRST|LAST)', sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'HIGH',
                'issue': 'Cursor Usage Detected',
                'impact': 'Cursors are slow and resource-intensive',
                'recommendation': 'Replace with SET-based operations',
                'example': '''
-- BAD:
DECLARE cursor_name CURSOR FOR SELECT ...
-- GOOD:
UPDATE t1 SET ... FROM table1 t1 INNER JOIN table2 t2 ...
                '''.strip()
            })
        
        return issues
    
    def detect_implicit_conversions(self, sql_text: str) -> List[Dict]:
        """Detect potential implicit conversions."""
        issues = []
        
        # Pattern 1: VARCHAR comparison with bare numbers (e.g., WHERE varchar_col = 123)
        if re.search(r"WHERE\s+\w+\s*=\s*\d+", sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'MEDIUM',
                'issue': 'Potential Implicit Conversion',
                'impact': 'Can prevent index usage',
                'recommendation': 'Ensure data types match in WHERE clauses',
                'example': '''
-- BAD:
WHERE varchar_column = 123
-- GOOD:
WHERE varchar_column = '123'
OR
WHERE int_column = 123
                '''.strip()
            })
        
        # Pattern 2: ID columns (UserId, OrderId, CustomerId) compared with STRING literals
        # This catches cases like: WHERE UserId = '123' (should be numeric)
        if re.search(r"WHERE\s+\w*(?:Id|ID)\w*\s*=\s*'[^']*'", sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'MEDIUM',
                'issue': 'Implicit Conversion on ID Column',
                'impact': 'String comparison on numeric ID column prevents index usage',
                'recommendation': 'Use numeric literals for ID columns',
                'example': '''
-- BAD:
WHERE UserId = '123'
-- GOOD:
WHERE UserId = 123
                '''.strip()
            })
        
        return issues
    
    def detect_scalar_functions(self, sql_text: str) -> List[Dict]:
        """Detect scalar functions in WHERE clause."""
        issues = []
        
        # Functions on columns in WHERE
        if re.search(r"WHERE\s+\w+\s*\(\s*\w+\s*\)", sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'MEDIUM',
                'issue': 'Function on Column in WHERE Clause',
                'impact': 'Prevents index usage (non-SARGable)',
                'recommendation': 'Avoid functions on columns in WHERE',
                'example': '''
-- BAD:
WHERE UPPER(name) = 'JOHN'
WHERE YEAR(date_column) = 2024
-- GOOD:
WHERE name = 'JOHN' (use case-insensitive collation)
WHERE date_column >= '2024-01-01' AND date_column < '2025-01-01'
                '''.strip()
            })
        
        return issues
    
    def detect_or_conditions(self, sql_text: str) -> List[Dict]:
        """Detect OR conditions that may impact performance."""
        issues = []
        
        or_count = len(re.findall(r'\bOR\b', sql_text, re.IGNORECASE))
        if or_count > 3:
            issues.append({
                'category': 'Performance',
                'severity': 'LOW',
                'issue': f'Multiple OR Conditions ({or_count} found)',
                'impact': 'May cause index scan instead of seek',
                'recommendation': 'Consider UNION ALL or IN clause',
                'example': '''
-- BAD:
WHERE col1 = 'A' OR col1 = 'B' OR col1 = 'C'
-- GOOD:
WHERE col1 IN ('A', 'B', 'C')
OR
WHERE col1 = 'A' UNION ALL SELECT ... WHERE col1 = 'B'
                '''.strip()
            })
        
        return issues
    
    def detect_leading_wildcards(self, sql_text: str) -> List[Dict]:
        """Detect LIKE with leading wildcard."""
        issues = []
        
        if re.search(r"LIKE\s+['\"]%", sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'MEDIUM',
                'issue': 'LIKE with Leading Wildcard',
                'impact': 'Cannot use index (table scan)',
                'recommendation': 'Avoid leading wildcards or use Full-Text Search',
                'example': '''
-- BAD:
WHERE name LIKE '%smith'
-- GOOD:
WHERE name LIKE 'smith%' (can use index)
OR use Full-Text Search for complex patterns
                '''.strip()
            })
        
        return issues
    
    def detect_select_into(self, sql_text: str) -> List[Dict]:
        """Detect SELECT INTO usage."""
        issues = []
        
        if re.search(r'\bSELECT\s+.*\s+INTO\s+', sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'LOW',
                'issue': 'SELECT INTO Usage',
                'impact': 'Can cause blocking and logging overhead',
                'recommendation': 'Consider CREATE TABLE + INSERT for production',
                'example': '''
-- OK for temp tables:
SELECT * INTO #temp FROM table1
-- For permanent tables, prefer:
CREATE TABLE dbo.NewTable (...);
INSERT INTO dbo.NewTable SELECT ...
                '''.strip()
            })
        
        return issues
    
    def calculate_performance_score(self, issues: List[Dict]) -> int:
        """Calculate performance score (0-100)."""
        score = 100
        
        for issue in issues:
            if issue['severity'] == 'HIGH':
                score -= 25
            elif issue['severity'] == 'MEDIUM':
                score -= 10
            elif issue['severity'] == 'LOW':
                score -= 5
        
        return max(0, score)
    
    def get_grade(self, score: int) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
