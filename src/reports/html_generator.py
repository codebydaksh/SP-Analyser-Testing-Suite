"""
HTML Report Generator
Creates beautiful, interactive HTML reports
"""
from datetime import datetime
from typing import Dict, Any

class HTMLReportGenerator:
    """Generate interactive HTML reports."""
    
    def generate(self, analysis_data: Dict[str, Any], sp_name: str) -> str:
        """Generate complete HTML report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Analysis Report - {sp_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white;
                      border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                      padding: 40px; }}
        h1 {{ color: #2d3748; margin-bottom: 10px; font-size: 2.5em; }}
        .timestamp {{ color: #718096; font-size: 0.9em; margin-bottom: 30px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                         gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 25px; border-radius: 10px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; margin: 10px 0; }}
        .metric-label {{ font-size: 0.9em; opacity: 0.9; text-transform: uppercase;
                         letter-spacing: 1px; }}
        .section {{ margin: 40px 0; }}
        .section-title {{ font-size: 1.8em; color: #2d3748; margin-bottom: 20px;
                          border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        .issue {{ background: #fff5f5; border-left: 4px solid #f56565; padding: 15px;
                  margin: 10px 0; border-radius: 5px; }}
        .issue.medium {{ background: #fffaf0; border-left-color: #ed8936; }}
        .issue.low {{ background: #f0fff4; border-left-color: #48bb78; }}
        .issue-header {{ display: flex; justify-content: space-between; align-items: center;
                         margin-bottom: 10px; }}
        .severity-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 0.8em;
                           font-weight: bold; text-transform: uppercase; }}
        .high {{ background: #f56565; color: white; }}
        .medium {{ background: #ed8936; color: white; }}
        .low {{ background: #48bb78; color: white; }}
        .grade {{ display: inline-block; width: 80px; height: 80px; line-height: 80px;
                  text-align: center; font-size: 2.5em; font-weight: bold;
                  border-radius: 50%; background: #667eea; color: white;
                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f7fafc; font-weight: 600; color: #2d3748; }}
        .good {{ color: #48bb78; font-weight: bold; }}
        .warning {{ color: #ed8936; font-weight: bold; }}
        .bad {{ color: #f56565; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stored Procedure Analysis Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div class="timestamp">Procedure: <strong>{sp_name}</strong></div>
        
        {self._generate_metrics_section(analysis_data)}
        {self._generate_security_section(analysis_data.get('security', {}))}
        {self._generate_quality_section(analysis_data.get('quality', {}))}
        {self._generate_complexity_section(analysis_data.get('complexity', {}))}
        {self._generate_dependencies_section(analysis_data.get('dependencies', {}))}
    </div>
</body>
</html>
"""
        return html
    
    def _generate_metrics_section(self, data: Dict) -> str:
        """Generate metrics cards."""
        security_score = data.get('security', {}).get('score', 0)
        quality_score = data.get('quality', {}).get('quality_score', 0)
        complexity = data.get('complexity', {}).get('complexity', 0)
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Security Score</div>
                <div class="metric-value">{security_score}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Code Quality</div>
                <div class="metric-value">{data.get('quality', {}).get('grade', 'N/A')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Complexity</div>
                <div class="metric-value">{complexity}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Lines of Code</div>
                <div class="metric-value">{data.get('basic', {}).get('lines_of_code', 0)}</div>
            </div>
        </div>
        """
    
    def _generate_security_section(self, security: Dict) -> str:
        """Generate security analysis section."""
        if not security:
            return ""
        
        issues_html = ""
        for issue in security.get('sql_injection_risks', []) + security.get('permission_issues', []):
            issues_html += f"""
            <div class="issue {issue['severity'].lower()}">
                <div class="issue-header">
                    <strong>{issue['type']}</strong>
                    <span class="severity-badge {issue['severity'].lower()}">{issue['severity']}</span>
                </div>
                <div>{issue['message']}</div>
                <div style="margin-top: 8px; color: #4a5568;"><strong>Recommendation:</strong> {issue['recommendation']}</div>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-title">🔒 Security Analysis</div>
            {issues_html if issues_html else '<p class="good">✓ No security issues detected</p>'}
        </div>
        """
    
    def _generate_quality_section(self, quality: Dict) -> str:
        """Generate code quality section."""
        if not quality:
            return ""
        
        issues_html = ""
        for issue in quality.get('issues', []):
            issues_html += f"""
            <div class="issue {issue['severity'].lower()}">
                <div class="issue-header">
                    <strong>{issue['category']}</strong>
                    <span class="severity-badge {issue['severity'].lower()}">{issue['severity']}</span>
                </div>
                <div>{issue['message']}</div>
                <div style="margin-top: 8px; color: #4a5568;"><strong>Recommendation:</strong> {issue['recommendation']}</div>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-title">⭐ Code Quality</div>
            <div style="margin: 20px 0;">
                <span class="grade">{quality.get('grade', 'N/A')}</span>
                <span style="margin-left: 20px; font-size: 1.2em;">Score: {quality.get('quality_score', 0)}/100</span>
            </div>
            {issues_html if issues_html else '<p class="good">✓ No quality issues detected</p>'}
        </div>
        """
    
    def _generate_complexity_section(self, complexity: Dict) -> str:
        """Generate complexity metrics section."""
        if not complexity:
            return ""
        
        return f"""
        <div class="section">
            <div class="section-title">Complexity Metrics</div>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Cyclomatic Complexity</td><td>{complexity.get('complexity', 0)}</td></tr>
                <tr><td>Code Blocks</td><td>{complexity.get('code_blocks', 0)}</td></tr>
                <tr><td>IF Statements</td><td>{complexity.get('if_statements', 0)}</td></tr>
                <tr><td>WHILE Loops</td><td>{complexity.get('while_loops', 0)}</td></tr>
            </table>
        </div>
        """
    
    def _generate_dependencies_section(self, deps: Dict) -> str:
        """Generate dependencies section."""
        if not deps:
            return ""
        
        tables_html = "<br>".join(deps.get('tables', [])) or 'None'
        procs_html = "<br>".join(deps.get('procedures', [])) or 'None'
        
        return f"""
        <div class="section">
            <div class="section-title">🔗 Dependencies</div>
            <table>
                <tr><th>Type</th><th>Dependencies</th></tr>
                <tr><td><strong>Tables</strong></td><td>{tables_html}</td></tr>
                <tr><td><strong>Procedures</strong></td><td>{procs_html}</td></tr>
            </table>
        </div>
        """
