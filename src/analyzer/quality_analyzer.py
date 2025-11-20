"""
Code Quality Analyzer for T-SQL
Best practices, naming conventions, code smells
"""
import re
from typing import List, Dict

class CodeQualityAnalyzer:
    """Analyze T-SQL code quality and best practices."""
    
    def analyze(self, sql_text: str, sp_name: str) -> Dict:
        """Run all quality checks."""
        issues = []
        
        # Naming conventions
        issues.extend(self.check_naming_conventions(sql_text, sp_name))
        
        # Code smells
        issues.extend(self.check_code_smells(sql_text))
        
        # Best practices
        issues.extend(self.check_best_practices(sql_text))
        
        # Calculate quality score
        score = self.calculate_quality_score(sql_text, issues)
        
        return {
            'issues': issues,
            'quality_score': score,
            'grade': self.get_grade(score)
        }
    
    def check_naming_conventions(self, sql_text: str, sp_name: str) -> List[Dict]:
        """Check naming convention compliance."""
        issues = []
        
        # SP should start with usp_, sp_, or proc_
        if not re.match(r'(usp_|sp_|proc_)', sp_name, re.IGNORECASE):
            issues.append({
                'category': 'Naming',
                'severity': 'LOW',
                'message': f'SP name "{sp_name}" doesn\'t follow usp_/sp_/proc_ convention',
                'recommendation': 'Use consistent prefix for stored procedures'
            })
        
        # Parameters should start with @
        params = re.findall(r'DECLARE\s+(\w+)', sql_text, re.IGNORECASE)
        for param in params:
            if not param.startswith('@'):
                issues.append({
                    'category': 'Naming',
                    'severity': 'LOW',
                    'message': f'Variable "{param}" should start with @',
                    'recommendation': 'Use @ prefix for all variables'
                })
        
        return issues
    
    def check_code_smells(self, sql_text: str) -> List[Dict]:
        """Detect code smells."""
        issues = []
        
        # SELECT *
        if re.search(r'SELECT\s+\*', sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Performance',
                'severity': 'MEDIUM',
                'message': 'SELECT * detected',
                'recommendation': 'Specify column names explicitly for better performance'
            })
        
        # Missing WHERE clause in UPDATE/DELETE
        if re.search(r'UPDATE\s+\w+\s+SET\s+[^W]+(?:;|$)', sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Risk',
                'severity': 'HIGH',
                'message': 'UPDATE without WHERE clause',
                'recommendation': 'Always use WHERE clause to prevent unintended updates'
            })
        
        if re.search(r'DELETE\s+FROM\s+\w+\s*(?:;|$)', sql_text, re.IGNORECASE):
            issues.append({
                'category': 'Risk',
                'severity': 'HIGH',
                'message': 'DELETE without WHERE clause',
                'recommendation': 'Always use WHERE clause to prevent data loss'
            })
        
        # NOLOCK hint overuse
        nolock_count = len(re.findall(r'WITH\s*\(NOLOCK\)', sql_text, re.IGNORECASE))
        if nolock_count > 3:
            issues.append({
                'category': 'Consistency',
                'severity': 'MEDIUM',
                'message': f'NOLOCK hint used {nolock_count} times',
                'recommendation': 'Review necessity - may lead to dirty reads'
            })
        
        return issues
    
    def check_best_practices(self, sql_text: str) -> List[Dict]:
        """Check T-SQL best practices."""
        issues = []
        
        # SET NOCOUNT ON
        if 'SET NOCOUNT ON' not in sql_text.upper():
            issues.append({
                'category': 'Performance',
                'severity': 'LOW',
                'message': 'Missing SET NOCOUNT ON',
                'recommendation': 'Add SET NOCOUNT ON to reduce network traffic'
            })
        
        # Missing schema qualification
        if re.search(r'FROM\s+(\w+)\s+(?!\.)', sql_text, re.IGNORECASE):
            unqualified_tables = re.findall(r'FROM\s+(\w+)(?!\s*\.)', sql_text, re.IGNORECASE)
            if unqualified_tables and len([t for t in unqualified_tables if not t.upper() in ['DUAL', 'DELETED', 'INSERTED']]) > 0:
                issues.append({
                    'category': 'Best Practice',
                    'severity': 'LOW',
                    'message': 'Tables without schema qualification',
                    'recommendation': 'Always specify schema (e.g., dbo.TableName)'
                })
        
        # No transaction for DML operations
        has_dml = bool(re.search(r'\b(INSERT|UPDATE|DELETE)\b', sql_text, re.IGNORECASE))
        has_transaction = bool(re.search(r'BEGIN\s+TRAN', sql_text, re.IGNORECASE))
        
        if has_dml and not has_transaction:
            issues.append({
                'category': 'Data Integrity',
                'severity': 'MEDIUM',
                'message': 'DML operations without explicit transaction',
                'recommendation': 'Wrap DML in BEGIN TRAN...COMMIT/ROLLBACK'
            })
        
        return issues
    
    def calculate_quality_score(self, sql_text: str, issues: List[Dict]) -> int:
        """Calculate overall quality score (0-100)."""
        score = 100
        
        for issue in issues:
            if issue['severity'] == 'HIGH':
                score -= 15
            elif issue['severity'] == 'MEDIUM':
                score -= 8
            elif issue['severity'] == 'LOW':
                score -= 3
        
        # Bonus for good practices
        if 'SET NOCOUNT ON' in sql_text.upper():
            score += 5
        if 'BEGIN TRY' in sql_text.upper():
            score += 5
        if 'BEGIN TRAN' in sql_text.upper():
            score += 5
        
        return max(0, min(100, score))
    
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
