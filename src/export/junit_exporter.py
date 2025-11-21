"""
JUnit XML Exporter for CI/CD Integration

Exports test results and analysis to JUnit XML format for:
- Jenkins
- GitHub Actions
- Azure DevOps
- GitLab CI
"""
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
from datetime import datetime
import re


class JUnitExporter:
    """Export test results and analysis findings to JUnit XML format."""
    
    def __init__(self):
        self.test_suite_name = "T-SQL Analysis"
    
    def export_analysis_as_tests(self, sp_analysis: Dict[str, Any]) -> str:
        """
        Convert SP analysis results into JUnit XML test cases.
        Each finding becomes a test case (PASS/FAIL based on severity).
        
        Args:
            sp_analysis: Full analysis result from SPAnalyzer
            
        Returns:
            JUnit XML string
        """
        proc_name = sp_analysis.get('procedure_name', 'Unknown')
        
        # Create root testsuite element
        testsuite = ET.Element('testsuite')
        testsuite.set('name', f"{self.test_suite_name} - {proc_name}")
        testsuite.set('timestamp', datetime.now().isoformat())
        
        test_cases = []
        failures = 0
        errors = 0
        
        # Security tests
        security_tests = self._create_security_tests(sp_analysis)
        test_cases.extend(security_tests)
        failures += sum(1 for tc in security_tests if tc.find('failure') is not None)
        
        # Quality tests
        quality_tests = self._create_quality_tests(sp_analysis)
        test_cases.extend(quality_tests)
        failures += sum(1 for tc in quality_tests if tc.find('failure') is not None)
        
        # Performance tests
        perf_tests = self._create_performance_tests(sp_analysis)
        test_cases.extend(perf_tests)
        failures += sum(1 for tc in perf_tests if tc.find('failure') is not None)
        
        # Add all test cases to suite
        for tc in test_cases:
            testsuite.append(tc)
        
        # Set suite attributes
        testsuite.set('tests', str(len(test_cases)))
        testsuite.set('failures', str(failures))
        testsuite.set('errors', str(errors))
        testsuite.set('skipped', '0')
        testsuite.set('time', '0.1')  # Static for analysis
        
        # Convert to string
        return self._prettify_xml(testsuite)
    
    def _create_security_tests(self, sp_analysis: Dict[str, Any]) -> List[ET.Element]:
        """Create test cases for security findings."""
        test_cases = []
        security = sp_analysis.get('security', {})
        score = security.get('score', 100)
        
        # Test 1: Overall security score
        tc = ET.Element('testcase')
        tc.set('classname', f"{self.test_suite_name}.Security")
        tc.set('name', 'SecurityScore')
        tc.set('time', '0.01')
        
        if score < 70:  # Fail if score below 70
            failure = ET.SubElement(tc, 'failure')
            failure.set('message', f'Security score {score} is below threshold 70')
            failure.set('type', 'SecurityViolation')
            failure.text = f"Security analysis found critical issues:\n{self._format_security_issues(security)}"
        
        test_cases.append(tc)
        
        # Test 2: SQL Injection risks
        sql_injection_risks = security.get('analysis', {}).get('sql_injection_risks', [])
        tc = ET.Element('testcase')
        tc.set('classname', f"{self.test_suite_name}.Security")
        tc.set('name', 'SQLInjectionRisks')
        tc.set('time', '0.01')
        
        high_risks = [r for r in sql_injection_risks if r.get('severity') == 'HIGH']
        if high_risks:
            failure = ET.SubElement(tc, 'failure')
            failure.set('message', f'Found {len(high_risks)} HIGH severity SQL injection risks')
            failure.set('type', 'SQLInjection')
            failure.text = "\n".join([f"- {r.get('message', 'Unknown')}" for r in high_risks])
        
        test_cases.append(tc)
        
        return test_cases
    
    def _create_quality_tests(self, sp_analysis: Dict[str, Any]) -> List[ET.Element]:
        """Create test cases for code quality findings."""
        test_cases = []
        quality = sp_analysis.get('quality', {})
        
        # Test 1: Overall quality score
        tc = ET.Element('testcase')
        tc.set('classname', f"{self.test_suite_name}.Quality")
        tc.set('name', 'QualityScore')
        tc.set('time', '0.01')
        
        score = quality.get('score', 100)
        if score < 70:
            failure = ET.SubElement(tc, 'failure')
            failure.set('message', f'Quality score {score} is below threshold 70')
            failure.set('type', 'QualityViolation')
        
        test_cases.append(tc)
        
        # Test 2: Error handling
        tc = ET.Element('testcase')
        tc.set('classname', f"{self.test_suite_name}.Quality")
        tc.set('name', 'ErrorHandling')
        tc.set('time', '0.01')
        
        has_try_catch = sp_analysis.get('has_try_catch', False)
        if not has_try_catch:
            failure = ET.SubElement(tc, 'failure')
            failure.set('message', 'No TRY-CATCH block found')
            failure.set('type', 'MissingErrorHandling')
            failure.text = "Stored procedure lacks error handling. Add TRY-CATCH blocks."
        
        test_cases.append(tc)
        
        return test_cases
    
    def _create_performance_tests(self, sp_analysis: Dict[str, Any]) -> List[ET.Element]:
        """Create test cases for performance findings."""
        test_cases = []
        performance = sp_analysis.get('performance', {})
        
        # Test 1: Performance score
        tc = ET.Element('testcase')
        tc.set('classname', f"{self.test_suite_name}.Performance")
        tc.set('name', 'PerformanceScore')
        tc.set('time', '0.01')
        
        score = performance.get('score', 100)
        if score < 70:
            failure = ET.SubElement(tc, 'failure')
            failure.set('message', f'Performance score {score} is below threshold 70')
            failure.set('type', 'PerformanceIssue')
            
            issues = performance.get('issues', [])
            failure.text = "\n".join([f"- {i.get('issue', 'Unknown')}" for i in issues])
        
        test_cases.append(tc)
        
        return test_cases
    
    def _format_security_issues(self, security: Dict) -> str:
        """Format security issues for failure message."""
        issues = []
        analysis = security.get('analysis', {})
        
        for issue_type in ['sql_injection_risks', 'permission_issues', 'security_warnings']:
            items = analysis.get(issue_type, [])
            for item in items:
                issues.append(f"[{item.get('severity', 'UNKNOWN')}] {item.get('message', 'No message')}")
        
        return "\n".join(issues) if issues else "No specific issues listed"
    
    def _prettify_xml(self, element: ET.Element) -> str:
        """Convert XML element to pretty string."""
        # Add XML declaration
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(element, encoding='unicode')
        return xml_str
    
    def export_to_file(self, sp_analysis: Dict[str, Any], filename: str):
        """
        Export analysis to JUnit XML file.
        
        Args:
            sp_analysis: Analysis results
            filename: Output filename (e.g., 'junit-results.xml')
        """
        xml_content = self.export_analysis_as_tests(sp_analysis)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return filename
