"""
Demo: JUnit XML Export for CI/CD

Shows how analysis results can be exported as JUnit XML
for integration with Jenkins, GitHub Actions, Azure DevOps
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.export.junit_exporter import JUnitExporter


def main():
    exporter = JUnitExporter()
    
    print("="*80)
    print("JUNIT XML EXPORTER - CI/CD Integration")
    print("="*80)
    
    # Sample analysis result with some failures
    sample_analysis = {
        'procedure_name': 'dbo.ProcessPayment',
        'security': {
            'score': 55,  # Below threshold - will FAIL
            'analysis': {
                'sql_injection_risks': [
                    {
                        'severity': 'HIGH',
                        'type': 'Dynamic SQL',
                        'message': 'Dynamic SQL with string concatenation detected'
                    },
                    {
                        'severity': 'MEDIUM',
                        'type': 'String Concatenation',
                        'message': 'Parameter values concatenated into SQL string'
                    }
                ],
                'permission_issues': [],
                'security_warnings': []
            }
        },
        'quality': {
            'score': 85,  # Pass
            'grade': 'B'
        },
        'performance': {
            'score': 60,  # Below threshold - will FAIL
            'grade': 'D',
            'issues': [
                {
                    'category': 'Performance',
                    'severity': 'HIGH',
                    'issue': 'Cursor Usage Detected',
                    'impact': 'Cursors cause row-by-row processing',
                    'recommendation': 'Use SET-based operations'
                }
            ]
        },
        'has_try_catch': False  # Missing - will FAIL
    }
    
    print("\n📊 Sample Analysis Result:")
    print(f"   Procedure: {sample_analysis['procedure_name']}")
    print(f"   Security Score: {sample_analysis['security']['score']} (Threshold: 70)")
    print(f"   Quality Score: {sample_analysis['quality']['score']} (Threshold: 70)")
    print(f"   Performance Score: {sample_analysis['performance']['score']} (Threshold: 70)")
    print(f"   Error Handling: {'Yes' if sample_analysis['has_try_catch'] else 'No'}")
    
    # Export to JUnit XML
    print("\n\n📝 Generating JUnit XML...")
    junit_xml = exporter.export_analysis_as_tests(sample_analysis)
    
    print("\n" + "-"*80)
    print("JUNIT XML OUTPUT:")
    print("-"*80)
    print(junit_xml)
    
    # Save to file
    output_file = 'junit-results.xml'
    exporter.export_to_file(sample_analysis, output_file)
    print(f"\n✅ Saved to: {output_file}")
    
    print("\n" + "="*80)
    print("CI/CD Integration Ready!")
    print("="*80)
    print("\nUsage in CI/CD pipelines:")
    print("  ✓ Jenkins: Publish JUnit test result report")
    print("  ✓ GitHub Actions: upload junit-results.xml as artifact")
    print("  ✓ Azure DevOps: Publish Test Results task")
    print("  ✓ GitLab CI: artifacts:reports:junit")
    print("\nTest Results Summary:")
    print("  • Security: FAIL (score 55 < 70)")
    print("  • Quality: PASS (score 85 >= 70)")
    print("  • Performance: FAIL (score 60 < 70)")
    print("  • Error Handling: FAIL (no TRY-CATCH)")


if __name__ == '__main__':
    main()
