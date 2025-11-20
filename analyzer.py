#!/usr/bin/env python
"""
SQL Server Stored Procedure Analysis & Testing Suite
Complete CLI Interface with all features
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser.sp_parser import SPParser
from analyzer.dependency_resolver import DependencyResolver
from analyzer.cfg_builder import CFGBuilder
from analyzer.test_generator import SPTestGenerator
from parser.control_flow_extractor import ControlFlowExtractor
from analyzer.path_analyzer import PathAnalyzer
from analyzer.logic_explainer import LogicExplainer
from analyzer.visualizer import Visualizer

def analyze_command(args):
    """Comprehensive stored procedure analysis."""
    print(f"Analyzing: {args.file}")
    
    with open(args.file, 'r') as f:
        sql_code = f.read()
    
    parser = SPParser()
    try:
        ast = parser.parse(sql_code)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    print("\n=== Dependencies ===")
    resolver = DependencyResolver()
    deps = resolver.get_dependencies(ast)
    print(f"Tables: {', '.join(deps['tables']) if deps['tables'] else 'None'}")
    print(f"Procedures: {', '.join(deps['procedures']) if deps['procedures'] else 'None'}")
    
    print("\n=== Control Flow ===")
    cf_extractor = ControlFlowExtractor()
    control_flow = cf_extractor.extract_all(sql_code)
    print(f"IF blocks: {len(control_flow['if_blocks'])}")
    for block in control_flow['if_blocks']:
        print(f"  Line {block['line']}: IF {block['condition'][:50]}...")
    print(f"WHILE loops: {len(control_flow['while_loops'])}")
    for loop in control_flow['while_loops']:
        print(f"  Line {loop['line']}: WHILE {loop['condition'][:50]}...")
    
    print("\n=== CFG Analysis ===")
    builder = CFGBuilder()
    cfg = builder.build_from_source(sql_code)
    print(f"Total Nodes: {len(cfg.nodes)}")
    
    analyzer = PathAnalyzer()
    unreachable = analyzer.detect_unreachable(cfg)
    if unreachable:
        print(f"WARNING: {len(unreachable)} unreachable blocks!")
    else:
        print("No unreachable code")
    
    infinite_loops = analyzer.detect_infinite_loops(cfg)
    if infinite_loops:
        print(f"WARNING: {len(infinite_loops)} potential infinite loops!")
    else:
        print("No infinite loops")
    
    print("\n=== Complexity Metrics ===")
    explainer = LogicExplainer()
    summary = explainer.summarize_control_flow(cfg)
    print(f"Cyclomatic Complexity: {summary['complexity']}")
    print(f"Code Blocks: {summary['code_blocks']}")
    print(f"IF Statements: {summary['if_statements']}")
    print(f"WHILE Loops: {summary['while_loops']}")
    
    if args.visualize:
        viz = Visualizer()
        dot_file = args.file.replace('.sql', '_cfg.dot')
        viz.save_dot(cfg, dot_file)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"Analysis Report\n{'='*60}\n\n")
            f.write(f"Tables: {', '.join(deps['tables'])}\n")
            f.write(f"Procedures: {', '.join(deps['procedures'])}\n")
            f.write(f"\nIF blocks: {len(control_flow['if_blocks'])}\n")
            f.write(f"WHILE loops: {len(control_flow['while_loops'])}\n")
            f.write(f"\nComplexity: {summary['complexity']}\n")
            f.write(f"Unreachable: {len(unreachable)}\n")
        print(f"\nReport saved: {args.output}")
    
    return 0

def test_command(args):
    """Generate unit tests."""
    print(f"Generating tests: {args.file}")
    
    with open(args.file, 'r') as f:
        sql_code = f.read()
    
    parser = SPParser()
    ast = parser.parse(sql_code)
    
    proc_name = Path(args.file).stem
    generator = SPTestGenerator()
    params = generator.extract_parameters(ast)
    
    tests = generator.generate_tsqlt_tests(proc_name, params) if args.format == 'tsqlt' else generator.generate_ssdt_tests(proc_name, params)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(tests)
        print(f"Tests saved: {args.output}")
    else:
        print(tests)
    
    return 0

def main():
    parser = argparse.ArgumentParser(description='SP Analysis Suite')
    subparsers = parser.add_subparsers(dest='command')
    
    analyze = subparsers.add_parser('analyze', help='Analyze SP')
    analyze.add_argument('file', help='SQL file path')
    analyze.add_argument('--output', '-o', help='Report file')
    analyze.add_argument('--visualize', '-v', action='store_true', help='Generate DOT file')
    
    test = subparsers.add_parser('test', help='Generate tests')
    test.add_argument('file', help='SQL file path')
    test.add_argument('--format', '-f', choices=['tsqlt', 'ssdt'], default='tsqlt')
    test.add_argument('--output', '-o', help='Test file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return analyze_command(args) if args.command == 'analyze' else test_command(args)

if __name__ == '__main__':
    sys.exit(main())
