"""
CSV Batch Summary Generator
Creates Excel-friendly CSV summaries for batch analysis
"""
import csv
from typing import List, Dict

class CSVSummaryGenerator:
    """Generate CSV batch summaries."""
    
    def generate(self, results: List[Dict], output_file: str):
        """Generate CSV summary from batch results."""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Procedure Name',
                'File',
                'LOC',
                'Security Score',
                'Quality Grade',
                'Quality Score',
                'Performance Score',
                'Complexity',
                'Tables',
                'Procedures',
                'Security Issues',
                'Quality Issues',
                'Performance Issues',
                'Status'
            ])
            
            # Data rows
            for result in results:
                security_issues = len(result.get('security', {}).get('sql_injection_risks', [])) + \
                                len(result.get('security', {}).get('permission_issues', []))
                quality_issues = len(result.get('quality', {}).get('issues', []))
                perf_issues = len(result.get('performance', {}).get('issues', []))
                
                status = 'PASS'
                if result.get('security', {}).get('score', 100) < 70:
                    status = 'FAIL-SECURITY'
                elif result.get('quality', {}).get('quality_score', 100) < 70:
                    status = 'FAIL-QUALITY'
                elif perf_issues > 5:
                    status = 'WARN-PERFORMANCE'
                
                writer.writerow([
                    result.get('sp_name', 'Unknown'),
                    result.get('source', 'Unknown'),
                    result.get('basic', {}).get('lines_of_code', 0),
                    result.get('security', {}).get('score', 0),
                    result.get('quality', {}).get('grade', 'N/A'),
                    result.get('quality', {}).get('quality_score', 0),
                    result.get('performance', {}).get('performance_score', 0),
                    result.get('complexity', {}).get('complexity', 0),
                    len(result.get('dependencies', {}).get('tables', [])),
                    len(result.get('dependencies', {}).get('procedures', [])),
                    security_issues,
                    quality_issues,
                    perf_issues,
                    status
                ])
