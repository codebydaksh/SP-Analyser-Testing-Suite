"""
Vercel Serverless Function for T-SQL Analyzer
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.parser.tsql_text_parser import TSQLTextParser
    from src.analyzer.security_analyzer import SecurityAnalyzer
    from src.analyzer.quality_analyzer import CodeQualityAnalyzer
    from src.analyzer.performance_analyzer import PerformanceAnalyzer
except ImportError as e:
    # Fallback: add src directory explicitly
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    sys.path.insert(0, src_path)
    from parser.tsql_text_parser import TSQLTextParser
    from analyzer.security_analyzer import SecurityAnalyzer
    from analyzer.quality_analyzer import CodeQualityAnalyzer
    from analyzer.performance_analyzer import PerformanceAnalyzer

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
                'example': 'curl -X POST https://sp-analyser-testing-suite.vercel.app/api/analyze -H "Content-Type: application/json" -d \'{"sql":"CREATE PROCEDURE dbo.Test AS BEGIN SELECT 1; END"}\''
            }
        }
        
        self.wfile.write(json.dumps(info, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests to analyze SQL code."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, 'No content provided')
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            sql_code = data.get('sql', '')
            
            if not sql_code:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No SQL code provided in "sql" field'}).encode())
                return
            
            # Run analysis
            parser = TSQLTextParser()
            security = SecurityAnalyzer()
            quality = CodeQualityAnalyzer()
            performance = PerformanceAnalyzer()
            
            quality_result = quality.analyze(sql_code)
            performance_result = performance.analyze(sql_code)
            
            result = {
                'success': True,
                'procedure_name': parser.extract_procedure_name(sql_code),
                'parameters': parser.extract_parameters(sql_code),
                'tables': parser.extract_tables(sql_code),
                'security': {
                    'score': security.get_security_score(sql_code),
                    'analysis': security.analyze(sql_code)
                },
                'quality': {
                    'score': quality_result.get('quality_score', 0),
                    'grade': quality_result.get('grade', 'F'),
                    'issues': quality_result.get('issues', [])
                },
                'performance': {
                    'score': performance_result.get('performance_score', 0),
                    'grade': performance_result.get('grade', 'F'),
                    'issues': performance_result.get('issues', [])
                }
            }
            
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
