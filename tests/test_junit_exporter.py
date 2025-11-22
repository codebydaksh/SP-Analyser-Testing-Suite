"""
Comprehensive tests for JUnitExporter - Target 90%+ coverage
"""
import pytest
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from export.junit_exporter import JUnitExporter


class TestJUnitExporter:
    """Test suite for JUnit XML export functionality"""
    
    def test_basic_export(self):
        """Test basic export with minimal data"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'TestProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        assert xml_output is not None
        assert '<testsuite' in xml_output
        assert 'TestProc' in xml_output
    
    def test_security_failures_create_test_cases(self):
        """Test that security issues create failing test cases"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'InsecureProc',
            'security': {
                'score': 50,
                'analysis': {
                    'sql_injection_risks': [
                        {'severity': 'HIGH', 'message': 'SQL injection risk', 'type': 'Dynamic SQL'}
                    ]
                }
            },
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        # Should have failures
        root = ET.fromstring(xml_output)
        failures = int(root.get('failures', '0'))
        assert failures > 0
        
        # Should have failure element
        assert '<failure' in xml_output
    
    def test_quality_issues_create_test_cases(self):
        """Test that quality issues create test cases"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'LowQualityProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {
                'score': 60,
                'issues': [
                    {'severity': 'MEDIUM', 'message': 'Missing SET NOCOUNT ON', 'category': 'Best Practice'}
                ]
            },
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        root = ET.fromstring(xml_output)
        test_cases = root.findall('testcase')
        assert len(test_cases) > 0
    
    def test_performance_issues_create_test_cases(self):
        """Test that performance issues create test cases"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'SlowProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {
                'score': 60,
                'issues': [
                    {'severity': 'HIGH', 'issue': 'Cursor usage', 'category': 'Performance'}
                ]
            }
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        root = ET.fromstring(xml_output)
        failures = int(root.get('failures', '0'))
        assert failures > 0
    
    def test_valid_xml_structure(self):
        """Test that output is valid XML"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'ValidXMLProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        # Should parse without error
        root = ET.fromstring(xml_output)
        assert root.tag == 'testsuite'
        assert 'name' in root.attrib
        assert 'tests' in root.attrib
    
    def test_test_count_accurate(self):
        """Test that test count matches actual test cases"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'CountProc',
            'security': {
                'score': 70,
                'analysis': {
                    'sql_injection_risks': [
                        {'severity': 'HIGH', 'message': 'Risk 1', 'type': 'Type1'},
                        {'severity': 'MEDIUM', 'message': 'Risk 2', 'type': 'Type2'}
                    ]
                }
            },
            'quality': {
                'score': 70,
                'issues': [
                    {'severity': 'LOW', 'message': 'Issue 1', 'category': 'Cat1'}
                ]
            },
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        root = ET.fromstring(xml_output)
        reported_count = int(root.get('tests', '0'))
        actual_count = len(root.findall('testcase'))
        
        assert reported_count == actual_count
        assert actual_count >= 3  # At least security + quality tests
    
    def test_failure_count_accurate(self):
        """Test that failure count is accurate"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'FailureCountProc',
            'security': {
                'score': 60,
                'analysis': {
                    'sql_injection_risks': [
                        {'severity': 'CRITICAL', 'message': 'Critical risk', 'type': 'SQL'}
                    ]
                }
            },
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        root = ET.fromstring(xml_output)
        reported_failures = int(root.get('failures', '0'))
        
        # Count actual failure elements
        actual_failures = len([tc for tc in root.findall('testcase') if tc.find('failure') is not None])
        
        assert reported_failures == actual_failures
    
    def test_timestamp_present(self):
        """Test that timestamp is included"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'TimestampProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        root = ET.fromstring(xml_output)
        assert 'timestamp' in root.attrib
        assert root.get('timestamp') != ''
    
    def test_unknown_procedure_name(self):
        """Test handling of missing procedure name"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            # No procedure_name
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        assert 'Unknown' in xml_output
        root = ET.fromstring(xml_output)
        assert root.get('name') is not None
    
    def test_all_passing_tests(self):
        """Test scenario with all tests passing"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'PerfectProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []},
            'has_try_catch': True  # Need this to pass quality check
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        root = ET.fromstring(xml_output)
        failures = int(root.get('failures', '0'))
        tests = int(root.get('tests', '0'))
        
        # Should have tests and no failures
        assert tests > 0  # At least some baseline tests
        assert failures == 0  # All passing
    
    def test_multiple_severity_levels(self):
        """Test handling of different severity levels"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'MixedSeverityProc',
            'security': {
                'score': 50,
                'analysis': {
                    'sql_injection_risks': [
                        {'severity': 'CRITICAL', 'message': 'Critical', 'type': 'Type1'},
                        {'severity': 'HIGH', 'message': 'High', 'type': 'Type2'},
                        {'severity': 'MEDIUM', 'message': 'Medium', 'type': 'Type3'},
                        {'severity': 'LOW', 'message': 'Low', 'type': 'Type4'}
                    ]
                }
            },
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        # All should be represented
        assert 'CRITICAL' in xml_output or 'Critical' in xml_output
        assert 'HIGH' in xml_output or 'High' in xml_output
    
    def test_xml_special_characters_escaped(self):
        """Test that special XML characters are escaped"""
        exporter = JUnitExporter()
        
        sp_analysis = {
            'procedure_name': 'Special<>&Chars',
            'security': {
                'score': 50,
                'analysis': {
                    'sql_injection_risks': [
                        {'severity': 'HIGH', 'message': 'Risk with <tags> & "quotes"', 'type': 'Test'}
                    ]
                }
            },
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        # Should be valid XML despite special chars
        root = ET.fromstring(xml_output)
        assert root is not None
    
    def test_custom_test_suite_name(self):
        """Test custom test suite name"""
        exporter = JUnitExporter()
        exporter.test_suite_name = "Custom Test Suite"
        
        sp_analysis = {
            'procedure_name': 'CustomProc',
            'security': {'score': 100, 'analysis': {'sql_injection_risks': []}},
            'quality': {'score': 100, 'issues': []},
            'performance': {'score': 100, 'issues': []}
        }
        
        xml_output = exporter.export_analysis_as_tests(sp_analysis)
        
        assert 'Custom Test Suite' in xml_output
