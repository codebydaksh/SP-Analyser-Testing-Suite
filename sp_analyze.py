#!/usr/bin/env python
"""
SQL Server Stored Procedure Analysis & Testing Suite
WORLD-CLASS ENTERPRISE EDITION
Complete analysis with security, quality, performance insights
"""
import argparse
import sys
import json
from pathlib import Path
from glob import glob

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser.tsql_text_parser import TSQLTextParser
from parser.control_flow_extractor import ControlFlowExtractor
from analyzer.security_analyzer import SecurityAnalyzer
from analyzer.quality_analyzer import CodeQualityAnalyzer
from analyzer.performance_analyzer import PerformanceAnalyzer
from analyzer.cfg_builder import CFGBuilder
from analyzer.path_analyzer import PathAnalyzer
from analyzer.logic_explainer import LogicExplainer
from analyzer.visualizer import Visualizer
from analyzer.test_generator import SPTestGenerator
from reports.html_generator import HTMLReportGenerator
from reports.markdown_generator import MarkdownReportGenerator
from reports.csv_generator import CSVSummaryGenerator

class SPAnalyzer:
    """Main analyzer orchestrator."""
    
    def __init__(self):
        self.text_parser = TSQLTextParser()
        self.cf_extractor = ControlFlowExtractor()
        self.security_analyzer = SecurityAnalyzer()
        self.quality_analyzer = CodeQualityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
    
    def analyze_file(self, filepath: str) -> dict:
        """Comprehensive analysis of a single SP file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_text = f.read()
        
        return self.analyze_text(sql_text, filepath)
    
    def analyze_text(self, sql_text: str, source: str = "unknown") -> dict:
        """Analyze SQL text and return comprehensive results."""
        # Basic parsing
        basic_info = self.text_parser.parse(sql_text)
        sp_name = basic_info['name']
        
        # Control flow
        control_flow = self.cf_extractor.extract_all(sql_text)
        
        # CFG and path analysis
        builder = CFGBuilder()
        cfg = builder.build_from_source(sql_text)
        
        path_analyzer = PathAnalyzer()
        unreachable = path_analyzer.detect_unreachable(cfg)
        infinite_loops = path_analyzer.detect_infinite_loops(cfg)
        
        # Complexity
        explainer = LogicExplainer()
        complexity = explainer.summarize_control_flow(cfg)
        
        # Security analysis
        security = self.security_analyzer.analyze(sql_text)
        security['score'] = self.security_analyzer.get_security_score(sql_text)
        
        # Quality analysis
        quality = self.quality_analyzer.analyze(sql_text, sp_name)
        
        # Performance analysis (NEW!)
        performance = self.performance_analyzer.analyze(sql_text)
        
        return {
            'source': source,
            'sp_name': sp_name,
            'basic': basic_info,
            'control_flow': control_flow,
            'cfg_nodes': len(cfg.nodes),
            'unreachable_blocks': len(unreachable),
            'infinite_loops': len(infinite_loops),
            'complexity': complexity,
            'security': security,
            'quality': quality,
            'performance': performance,
            'dependencies': {
                'tables': basic_info['tables'],
                'procedures': basic_info['exec_calls']
            }
        }

def analyze_command(args):
    """Enhanced analyze command with all features."""
    analyzer = SPAnalyzer()
    
    # Batch mode or single file
    files = []
    if args.batch:
        files = glob(args.file)
        print(f"📂 Found {len(files)} files to analyze")
    else:
        files = [args.file]
    
    results = []
    for filepath in files:
        print(f"\n{'='*60}")
        print(f"Analyzing: {filepath}")
        print('='*60)
        
        try:
            result = analyzer.analyze_file(filepath)
            results.append(result)
            
            # Console output
            print_analysis_summary(result)
            
            # Generate reports
            if args.html:
                html_gen = HTMLReportGenerator()
                html_content = html_gen.generate(result, result['sp_name'])
                html_file = filepath.replace('.sql', '_report.html')
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"\nHTML report: {html_file}")
            
            if args.markdown:
                md_gen = MarkdownReportGenerator()
                md_content = md_gen.generate(result, result['sp_name'])
                md_file = filepath.replace('.sql', '_report.md')
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                print(f"Markdown report: {md_file}")
            
            if args.json:
                json_file = filepath.replace('.sql', '_analysis.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"JSON report: {json_file}")
            
            if args.visualize:
                builder = CFGBuilder()
                cfg = builder.build_from_source(open(filepath, 'r').read())
                viz = Visualizer()
                dot_file = filepath.replace('.sql', '_cfg.dot')
                viz.save_dot(cfg, dot_file)
        
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            if args.strict:
                return 1
    
    # Batch summary
    if len(results) > 1:
        print_batch_summary(results)
        
        # Export CSV summary if requested
        if args.csv:
            csv_gen = CSVSummaryGenerator()
            csv_gen.generate(results, args.csv)
            print(f"\nCSV summary: {args.csv}")
    
    # CI/CD integration - exit code based on thresholds
    if args.fail_on_quality and any(r['quality']['quality_score'] < args.min_quality for r in results):
        print(f"\nQuality threshold not met (minimum: {args.min_quality})")
        return 1
    
    if args.fail_on_security and any(r['security']['score'] < args.min_security for r in results):
        print(f"\nSecurity threshold not met (minimum: {args.min_security})")
        return 1
    
    return 0

def print_analysis_summary(result: dict):
    """Print concise analysis summary."""
    print("\nANALYSIS SUMMARY")
    print(f"  Procedure: {result['sp_name']}")
    print(f"  Lines of Code: {result['basic']['lines_of_code']}")
    
    print("\nMETRICS")
    print(f"  Security Score: {result['security']['score']}/100")
    print(f"  Quality Grade: {result['quality']['grade']} ({result['quality']['quality_score']}/100)")
    print(f"  Performance Score: {result['performance']['performance_score']}/100 ({result['performance']['grade']})")
    print(f"  Complexity: {result['complexity']['complexity']}")
    
    print("\n🔗 DEPENDENCIES")
    print(f"  Tables: {len(result['dependencies']['tables'])}")
    print(f"  Procedures: {len(result['dependencies']['procedures'])}")
    
    # Warnings
    if result['unreachable_blocks'] > 0:
        print(f"\n⚠️  {result['unreachable_blocks']} unreachable code blocks")
    if result['infinite_loops'] > 0:
        print(f"⚠️  {result['infinite_loops']} potential infinite loops")
    
    # Issues summary
    total_issues = len(result['security']['sql_injection_risks']) + \
                   len(result['security']['permission_issues']) + \
                   len(result['quality']['issues'])
    
    if total_issues > 0:
        print(f"\n📋 FOUND {total_issues} ISSUES")
        print("   Run with --html for detailed report")

def print_batch_summary(results: list):
    """Print batch analysis summary."""
    print(f"\n{'='*60}")
    print(f"BATCH SUMMARY ({len(results)} files)")
    print('='*60)
    
    avg_security = sum(r['security']['score'] for r in results) / len(results)
    avg_quality = sum(r['quality']['quality_score'] for r in results) / len(results)
    total_issues = sum(len(r['security']['sql_injection_risks']) + 
                      len(r['quality']['issues']) for r in results)
    
    print(f"Average Security Score: {avg_security:.1f}/100")
    print(f"Average Quality Score: {avg_quality:.1f}/100")
    print(f"Total Issues: {total_issues}")

def test_command(args):
    """Generate unit tests."""
    analyzer = SPAnalyzer()
    result = analyzer.analyze_file(args.file)
    
    generator = SPTestGenerator()
    params = result['basic']['parameters']
    
    tests = generator.generate_tsqlt_tests(result['sp_name'], params) if args.format == 'tsqlt' \
            else generator.generate_ssdt_tests(result['sp_name'], params)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(tests)
        print(f"Tests saved: {args.output}")
    else:
        print(tests)
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='World-Class SQL SP Analysis Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # ANALYZE COMMAND
    analyze = subparsers.add_parser('analyze', help='Comprehensive SP analysis')
    analyze.add_argument('file', help='SQL file or pattern (use --batch for wildcards)')
    analyze.add_argument('--batch', '-b', action='store_true', help='Batch mode with wildcards')
    analyze.add_argument('--html', action='store_true', help='Generate HTML report')
    analyze.add_argument('--markdown', '-m', action='store_true', help='Generate Markdown report')
    analyze.add_argument('--json', action='store_true', help='Generate JSON report')
    analyze.add_argument('--csv', type=str, help='CSV batch summary file (batch mode only)')
    analyze.add_argument('--visualize', '-v', action='store_true', help='Generate CFG visualization')
    analyze.add_argument('--strict', action='store_true', help='Fail on first error')
    
    # CI/CD Integration
    analyze.add_argument('--fail-on-quality', action='store_true', help='Fail if quality below threshold')
    analyze.add_argument('--min-quality', type=int, default=70, help='Minimum quality score (default: 70)')
    analyze.add_argument('--fail-on-security', action='store_true', help='Fail if security below threshold')
    analyze.add_argument('--min-security', type=int, default=80, help='Minimum security score (default: 80)')
    analyze.add_argument('--fail-on-performance', action='store_true', help='Fail if performance below threshold')
    analyze.add_argument('--min-performance', type=int, default=70, help='Minimum performance score (default: 70)')
    
    # TEST COMMAND
    test = subparsers.add_parser('test', help='Generate unit tests')
    test.add_argument('file', help='SQL file path')
    test.add_argument('--format', '-f', choices=['tsqlt', 'ssdt'], default='tsqlt')
    test.add_argument('--output', '-o', help='Test output file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'analyze':
        return analyze_command(args)
    elif args.command == 'test':
        return test_command(args)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
