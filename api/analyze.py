"""
Vercel Serverless Function for T-SQL Analyzer
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.tsql_text_parser import TSQLTextParser
from analyzer.security_analyzer import SecurityAnalyzer
from analyzer.quality_analyzer import CodeQualityAnalyzer
from analyzer.performance_analyzer import PerformanceAnalyzer

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to analyze SQL code."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            sql_code = data.get('sql', '')
            
            if not sql_code:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No SQL code provided'}).encode())
                return
            
            # Run analysis
            parser = TSQLTextParser()
            security = SecurityAnalyzer()
            quality = CodeQualityAnalyzer()
            performance = PerformanceAnalyzer()
            
            result = {
                'procedure_name': parser.extract_procedure_name(sql_code),
                'parameters': parser.extract_parameters(sql_code),
                'tables': parser.extract_tables(sql_code),
                'security': {
                    'score': security.get_security_score(sql_code),
                    'analysis': security.analyze(sql_code)
                },
                'quality': {
                    'score': quality.analyze(sql_code)['quality_score'],
                    'grade': quality.analyze(sql_code)['grade']
                },
                'performance': {
                    'score': performance.analyze(sql_code)['performance_score'],
                    'grade': performance.analyze(sql_code)['grade']
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_GET(self):
        """Handle GET requests - return API info."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        info = {
            'name': 'T-SQL Analyzer API',
            'version': '1.0.0',
            'endpoints': {
                'POST /api/analyze': 'Analyze T-SQL stored procedure code',
            },
            'usage': {
                'method': 'POST',
                'body': {'sql': 'CREATE PROCEDURE ... AS BEGIN ... END'},
                'response': {
                    'procedure_name': 'string',
                    'parameters': 'array',
                    'tables': 'array',
                    'security': {'score': 'int', 'analysis': 'object'},
                    'quality': {'score': 'int', 'grade': 'string'},
                    'performance': {'score': 'int', 'grade': 'string'}
                }
            }
        }
        
        self.wfile.write(json.dumps(info, indent=2).encode())
