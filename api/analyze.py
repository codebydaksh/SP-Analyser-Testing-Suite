"""
Vercel Serverless Function for T-SQL Analyzer
Simplified version with embedded analysis logic
"""
from http.server import BaseHTTPRequestHandler
import json
import re

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - return API info."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        info = {
            'name': 'T-SQL Analyzer API',
            'version': '1.0.0',
            'status': 'online',
            'endpoints': {
                'POST /api/analyze': 'Analyze T-SQL stored procedure code',
            },
            'usage': {
                'method': 'POST',
                'body': {'sql': 'CREATE PROCEDURE ... AS BEGIN ... END'},
                'example': 'POST with JSON body containing "sql" field'
            },
            'github': 'https://github.com/codebydaksh/SP-Analyser-Testing-Suite'
        }
        
        self.wfile.write(json.dumps(info, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests to analyze SQL code or generate tests."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, 'No content provided')
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            sql_code = data.get('sql', '')
            action = data.get('action', 'analyze')
            
            if not sql_code:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No SQL code provided in "sql" field'}).encode())
                return
            
            # Check if this is a test generation request
            if action == 'generate-tests' or self.path == '/api/generate-tests':
                result = self.generate_tests(sql_code, data.get('format', 'tsqlt'))
            else:
                # Perform basic analysis
                result = self.analyze_sql(sql_code)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Invalid JSON: {str(e)}'}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Server error: {str(e)}',
                'type': type(e).__name__
            }).encode())
    
    def analyze_sql(self, sql_code):
        """Simplified SQL analysis"""
        # Extract procedure name
        proc_match = re.search(r'CREATE\s+PROC(?:EDURE)?\s+(\[?[\w\.\]]+)', sql_code, re.IGNORECASE)
        procedure_name = proc_match.group(1) if proc_match else 'Unknown'
        
        # Extract parameters
        params = []
        param_pattern = r'@(\w+)\s+(\w+(?:\(\d+(?:,\d+)?\))?)'
        for match in re.finditer(param_pattern, sql_code):
            params.append({
                'name': f'@{match.group(1)}',
                'type': match.group(2)
            })
        
        # Extract tables
        tables = []
        table_patterns = [
            r'FROM\s+([\w\.\[\]]+)',
            r'JOIN\s+([\w\.\[\]]+)',
            r'INTO\s+([\w\.\[\]]+)',
            r'UPDATE\s+([\w\.\[\]]+)'
        ]
        for pattern in table_patterns:
            for match in re.finditer(pattern, sql_code, re.IGNORECASE):
                table = match.group(1).strip('[]')
                if table and table not in tables:
                    tables.append(table)
        
        # Security analysis
        security_score = 100
        security_issues = []
        
        # Check for SQL injection risks
        if re.search(r'EXEC(?:UTE)?\s*\(\s*@', sql_code, re.IGNORECASE):
            security_score -= 20
            security_issues.append({
                'severity': 'HIGH',
                'type': 'Dynamic SQL',
                'message': 'Dynamic SQL with variables detected',
                'recommendation': 'Use sp_executesql with parameters'
            })
        
        if re.search(r'\+\s*@\w+\s*\+|@\w+\s*\+', sql_code, re.IGNORECASE):
            security_score -= 10
            security_issues.append({
                'severity': 'MEDIUM',
                'type': 'String Concatenation',
                'message': 'String concatenation detected',
                'recommendation': 'Use parameterized queries'
            })
        
        # Quality analysis
        lines = len([l for l in sql_code.split('\n') if l.strip()])
        quality_score = 100
        quality_issues = []
        
        if not re.search(r'BEGIN\s+TRY', sql_code, re.IGNORECASE):
            quality_score -= 10
            quality_issues.append({
                'category': 'Error Handling',
                'severity': 'MEDIUM',
                'message': 'No TRY-CATCH block found',
                'recommendation': 'Add error handling'
            })
        
        # Calculate grade
        if quality_score >= 90:
            grade = 'A'
        elif quality_score >= 80:
            grade = 'B'
        elif quality_score >= 70:
            grade = 'C'
        elif quality_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # Performance analysis
        perf_score = 100
        perf_issues = []
        
        if re.search(r'CURSOR', sql_code, re.IGNORECASE):
            perf_score -= 25
            perf_issues.append({
                'category': 'Performance',
                'severity': 'HIGH',
                'issue': 'Cursor Usage Detected',
                'impact': 'Cursors are slow',
                'recommendation': 'Use SET-based operations'
            })
        
        if perf_score >= 90:
            perf_grade = 'A'
        elif perf_score >= 80:
            perf_grade = 'B'
        elif perf_score >= 70:
            perf_grade = 'C'
        else:
            perf_grade = 'F'
        
        return {
            'success': True,
            'procedure_name': procedure_name,
            'parameters': params,
            'tables': tables,
            'lines_of_code': lines,
            'security': {
                'score': max(0, security_score),
                'analysis': {
                    'sql_injection_risks': security_issues,
                    'permission_issues': [],
                    'security_warnings': []
                }
            },
            'quality': {
                'score': max(0, quality_score),
                'grade': grade,
                'issues': quality_issues
            },
            'performance': {
                'score': max(0, perf_score),
                'grade': perf_grade,
                'issues': perf_issues
            }
        }
    
    def generate_tests(self, sql_code: str, format_type: str = 'tsqlt') -> dict:
        """Generate unit tests for the stored procedure."""
        # Extract procedure name
        proc_match = re.search(r'CREATE\s+PROC(?:EDURE)?\s+(\[?[\w\.\]]+)', sql_code, re.IGNORECASE)
        procedure_name = proc_match.group(1) if proc_match else 'Unknown'
        
        # Extract parameters (same logic as analyze_sql)
        params = []
        param_pattern = r'@(\w+)\s+(\w+(?:\(\d+(?:,\d+)?\))?)'
        for match in re.finditer(param_pattern, sql_code):
            params.append({
                'name': f'@{match.group(1)}',
                'type': match.group(2)
            })
        
        # Generate tests based on format
        if format_type == 'ssdt':
            tests = self._generate_ssdt_tests(procedure_name, params)
        else:
            tests = self._generate_tsqlt_tests(procedure_name, params)
        
        return {
            'success': True,
            'procedure_name': procedure_name,
            'format': format_type,
            'tests': tests
        }
    
    def _generate_tsqlt_tests(self, proc_name: str, parameters: list) -> str:
        """Generate tSQLt test suite."""
        test_class = f"Test{proc_name.replace('.', '_').replace('[', '').replace(']', '')}"
        
        tests = []
        tests.append(f"EXEC tSQLt.NewTestClass '{test_class}';")
        tests.append("GO\n")
        
        # Test 1: Basic execution
        tests.append(f"CREATE PROCEDURE [{test_class}].[test_BasicExecution]")
        tests.append("AS")
        tests.append("BEGIN")
        tests.append("    -- Arrange")
        tests.append("    -- Act")
        if parameters:
            param_values = ", ".join([self._get_default_value(p) for p in parameters])
            tests.append(f"    EXEC {proc_name} {param_values};")
        else:
            tests.append(f"    EXEC {proc_name};")
        tests.append("    -- Assert")
        tests.append("    -- Add assertions here")
        tests.append("END;")
        tests.append("GO\n")
        
        # Test 2: NULL parameters (if any)
        if parameters:
            tests.append(f"CREATE PROCEDURE [{test_class}].[test_NullParameters]")
            tests.append("AS")
            tests.append("BEGIN")
            tests.append("    -- Test with NULL parameters")
            null_params = ", ".join(["NULL" for _ in parameters])
            tests.append(f"    EXEC {proc_name} {null_params};")
            tests.append("END;")
            tests.append("GO\n")
        
        return "\n".join(tests)
    
    def _generate_ssdt_tests(self, proc_name: str, parameters: list) -> str:
        """Generate SSDT-compatible test suite."""
        tests = []
        tests.append(f"-- SSDT Test Suite for {proc_name}")
        tests.append(f"-- Run with: SqlCmd or SSDT Test Runner\n")
        
        tests.append(f"-- Test: Basic Execution")
        tests.append(f"DECLARE @result INT;")
        if parameters:
            param_values = ", ".join([self._get_default_value(p) for p in parameters])
            tests.append(f"EXEC @result = {proc_name} {param_values};")
        else:
            tests.append(f"EXEC @result = {proc_name};")
        tests.append(f"IF @result <> 0 THROW 50000, 'Test failed: Basic execution', 1;")
        tests.append(f"PRINT 'PASS: Basic execution';\n")
        
        return "\n".join(tests)
    
    def _get_default_value(self, param: dict) -> str:
        """Get a default test value for a parameter based on its type."""
        param_type = param.get('type', 'VARCHAR').upper()
        
        if 'INT' in param_type or 'NUMERIC' in param_type or 'DECIMAL' in param_type or 'BIGINT' in param_type or 'SMALLINT' in param_type or 'TINYINT' in param_type:
            return "1"
        elif 'VARCHAR' in param_type or 'CHAR' in param_type or 'TEXT' in param_type or 'NVARCHAR' in param_type or 'NCHAR' in param_type:
            return "'test'"
        elif 'DATE' in param_type or 'TIME' in param_type or 'DATETIME' in param_type:
            return "'2024-01-01'"
        elif 'BIT' in param_type:
            return "1"
        elif 'FLOAT' in param_type or 'REAL' in param_type or 'MONEY' in param_type:
            return "1.0"
        else:
            return "'default'"
