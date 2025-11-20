"""
Markdown Report Generator
Creates Markdown reports suitable for documentation
"""
from datetime import datetime
from typing import Dict, Any

class MarkdownReportGenerator:
    """Generate Markdown reports."""
    
    def generate(self, analysis_data: Dict[str, Any], sp_name: str) -> str:
        """Generate complete Markdown report."""
        lines = []
        
        lines.append(f"# Analysis Report: {sp_name}")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")
        
        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Procedure:** `{sp_name}`")
        lines.append(f"- **Lines of Code:** {analysis_data.get('basic', {}).get('lines_of_code', 0)}")
        lines.append(f"- **Security Score:** {analysis_data.get('security', {}).get('score', 0)}/100")
        lines.append(f"- **Quality Grade:** {analysis_data.get('quality', {}).get('grade', 'N/A')}")
        lines.append(f"- **Performance Score:** {analysis_data.get('performance', {}).get('performance_score', 'N/A')}/100")
        lines.append(f"- **Complexity:** {analysis_data.get('complexity', {}).get('complexity', 0)}")
        lines.append("\n")
        
        # Dependencies
        lines.append("## 🔗 Dependencies\n")
        deps = analysis_data.get('dependencies', {})
        lines.append(f"**Tables:** {len(deps.get('tables', []))}")
        for table in deps.get('tables', []):
            lines.append(f"- `{table}`")
        lines.append(f"\n**Procedures:** {len(deps.get('procedures', []))}")
        for proc in deps.get('procedures', []):
            lines.append(f"- `{proc}`")
        lines.append("\n")
        
        # Security Issues
        security = analysis_data.get('security', {})
        if security.get('sql_injection_risks') or security.get('permission_issues'):
            lines.append("## 🔒 Security Issues\n")
            for issue in security.get('sql_injection_risks', []):
                lines.append(f"### {issue['type']} [{issue['severity']}]")
                lines.append(f"> {issue['message']}")
                lines.append(f"\n**Recommendation:** {issue['recommendation']}\n")
        
        lines.append("\n")
        
        # Quality Issues
        quality = analysis_data.get('quality', {})
        if quality.get('issues'):
            lines.append("## Code Quality Issues\n")
            for issue in quality.get('issues'):
                lines.append(f"### {issue['category']} [{issue['severity']}]")
                lines.append(f"> {issue['message']}")
                lines.append(f"\n**Recommendation:** {issue['recommendation']}\n")
        
        # Performance Issues
        performance = analysis_data.get('performance', {})
        if performance.get('issues'):
            lines.append("## Performance Issues\n")
            for issue in performance.get('issues'):
                lines.append(f"### {issue['issue']} [{issue['severity']}]")
                lines.append(f"> **Impact:** {issue['impact']}")
                lines.append(f"\n**Recommendation:** {issue['recommendation']}")
                if 'example' in issue:
                    lines.append(f"\n```sql\n{issue['example']}\n```\n")
        
        # Metrics
        lines.append("## Metrics\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        complexity = analysis_data.get('complexity', {})
        lines.append(f"| Cyclomatic Complexity | {complexity.get('complexity', 0)} |")
        lines.append(f"| Code Blocks | {complexity.get('code_blocks', 0)} |")
        lines.append(f"| IF Statements | {complexity.get('if_statements', 0)} |")
        lines.append(f"| WHILE Loops | {complexity.get('while_loops', 0)} |")
        
        return "\n".join(lines)
