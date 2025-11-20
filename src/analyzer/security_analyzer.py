"""
Security Analyzer for T-SQL Stored Procedures
Detects SQL injection risks, permission issues, and security anti-patterns
"""
import re
from typing import List, Dict

class SecurityAnalyzer:
    """Analyze stored procedures for security vulnerabilities."""
    
    def __init__(self):
        # SQL Injection patterns
        self.dynamic_sql_pattern = re.compile(r'EXEC(?:UTE)?\s*\(?\s*@', re.IGNORECASE)
        self.concat_pattern = re.compile(r'\+\s*@\w+\s*\+|@\w+\s*\+', re.IGNORECASE)
        
    def analyze(self, sql_text: str) -> Dict[str, List[Dict]]:
        """Run all security checks."""
        return {
            'sql_injection_risks': self.detect_sql_injection(sql_text),
            'permission_issues': self.detect_permission_issues(sql_text),
            'security_warnings': self.detect_security_warnings(sql_text)
        }
    
    def detect_sql_injection(self, sql_text: str) -> List[Dict]:
        """Detect potential SQL injection vulnerabilities."""
        issues = []
        
        # Dynamic SQL execution
        if self.dynamic_sql_pattern.search(sql_text):
            issues.append({
                'severity': 'HIGH',
                'type': 'Dynamic SQL',
                'message': 'Dynamic SQL with variables detected - potential SQL injection risk',
                'recommendation': 'Use sp_executesql with parameters instead of EXEC(@sql)'
            })
        
        # String concatenation in SQL
        if self.concat_pattern.search(sql_text):
            issues.append({
                'severity': 'MEDIUM',
                'type': 'String Concatenation',
                'message': 'String concatenation detected - ensure proper sanitization',
                'recommendation': 'Use parameterized queries'
            })
        
        # sp_executesql with concatenation (enhanced check for tests)
        if re.search(r"sp_executesql\s+N?['\"].*?\+|sp_executesql.*?\+\s*(?:CAST|CONVERT)", sql_text, re.IGNORECASE):
            if not any(issue['type'] == 'Dynamic SQL' for issue in issues):
                issues.append({
                    'severity': 'HIGH',
                    'type': 'Dynamic SQL',
                    'message': 'sp_executesql with string concatenation detected',
                    'recommendation': 'Use sp_executesql with proper @params definition'
                })
        
        # Direct string comparison (potential injection)
        if re.search(r"WHERE\s+\w+\s*=\s*'\s*\+\s*@", sql_text, re.IGNORECASE):
            issues.append({
                'severity': 'HIGH',
                'type': 'Unsafe WHERE Clause',
                'message': 'WHERE clause with concatenated user input',
                'recommendation': 'Use parameterized WHERE conditions'
            })
        
        return issues
    
    def detect_permission_issues(self, sql_text: str) -> List[Dict]:
        """Detect permission and privilege issues."""
        issues = []
        
        # Usage of xp_ procedures (high privilege)
        if re.search(r'\bxp_\w+', sql_text, re.IGNORECASE):
            issues.append({
                'severity': 'HIGH',
                'type': 'Extended Stored Procedure',
                'message': 'Usage of xp_ extended procedures detected',
                'recommendation': 'Review necessity - these require elevated privileges'
            })
        
        # EXECUTE AS usage
        if re.search(r'EXECUTE\s+AS', sql_text, re.IGNORECASE):
            issues.append({
                'severity': 'MEDIUM',
                'type': 'Impersonation',
                'message': 'EXECUTE AS detected - context switching',
                'recommendation': 'Ensure minimal privilege escalation'
            })
        
        return issues
    
    def detect_security_warnings(self, sql_text: str) -> List[Dict]:
        """Detect general security warnings."""
        warnings = []
        
        # No TRY-CATCH error handling
        if 'BEGIN TRY' not in sql_text.upper():
            warnings.append({
                'severity': 'LOW',
                'type': 'Error Handling',
                'message': 'No TRY-CATCH block found',
                'recommendation': 'Add error handling to prevent information disclosure'
            })
        
        # Sensitive data in comments
        if re.search(r'--.*(?:password|secret|key|token)', sql_text, re.IGNORECASE):
            warnings.append({
                'severity': 'MEDIUM',
                'type': 'Sensitive Data',
                'message': 'Potential sensitive data in comments',
                'recommendation': 'Remove sensitive information from code'
            })
        
        return warnings
    
    def get_security_score(self, sql_text: str) -> int:
        """Calculate security score (0-100, higher is better)."""
        analysis = self.analyze(sql_text)
        
        score = 100
        
        # Deduct points for issues
        for issue in analysis['sql_injection_risks']:
            if issue['severity'] == 'HIGH':
                score -= 20
            elif issue['severity'] == 'MEDIUM':
                score -= 10
        
        for issue in analysis['permission_issues']:
            if issue['severity'] == 'HIGH':
                score -= 15
            elif issue['severity'] == 'MEDIUM':
                score -= 8
        
        for warning in analysis['security_warnings']:
            if warning['severity'] == 'MEDIUM':
                score -= 5
            elif warning['severity'] == 'LOW':
                score -= 2
        
        return max(0, score)
