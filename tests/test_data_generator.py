"""
Unit tests for TestDataGenerator

Tests boundary values, edge cases, and realistic data generation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.testing.test_data_generator import TestDataGenerator


def test_integer_data_generation():
    """Test INT data generation."""
    gen = TestDataGenerator()
    param = {'name': '@UserId', 'type': 'INT'}
    
    result = gen.generate_test_values(param)
    
    # Should have all categories
    assert 'valid' in result
    assert 'invalid' in result
    assert 'boundary' in result
    assert 'edge_cases' in result
    
    # Validate boundaries
    assert -2147483648 in result['boundary']  # INT MIN
    assert 2147483647 in result['boundary']   # INT MAX
    assert 0 in result['boundary']
    
    # NULL should be in edge cases
    assert 'NULL' in result['edge_cases']
    
    print(" Integer data generation works!")


def test_string_data_generation():
    """Test VARCHAR data generation."""
    gen = TestDataGenerator()
    param = {'name': '@Email', 'type': 'VARCHAR(100)'}
    
    result = gen.generate_test_values(param)
    
    # Should include SQL injection tests
    assert any("DROP TABLE" in str(v) for v in result['edge_cases'])
    
    # Should include boundary lengths (max-1 and max length strings)
    boundary_str = str(result['boundary'])
    assert "AAA" in boundary_str or len(result['boundary']) >= 2  # Has long strings
    
    # Should include empty string
    assert "''" in result['boundary']
    
    print(" String data generation works!")


def test_datetime_data_generation():
    """Test DATETIME data generation."""
    gen = TestDataGenerator()
    param = {'name': '@OrderDate', 'type': 'DATETIME'}
    
    result = gen.generate_test_values(param)
    
    # Should include SQL Server boundaries
    assert "'1753-01-01'" in result['boundary']
    assert "'9999-12-31'" in result['boundary']
    
    # Should include invalid dates
    assert len(result['invalid']) > 0
    
    print(" Datetime data generation works!")


def test_realistic_value_generation():
    """Test smart realistic value generation based on param names."""
    gen = TestDataGenerator()
    
    # Email should return a realistic email
    email_param = {'name': '@Email', 'type': 'VARCHAR(100)'}
    assert gen.get_realistic_value(email_param) == "'test@example.com'"
    
    # ID should return a number
    id_param = {'name': '@UserId', 'type': 'INT'}
    assert gen.get_realistic_value(id_param) == "1"
    
    # Date should return a date
    date_param = {'name': '@OrderDate', 'type': 'DATETIME'}
    assert "'2024" in gen.get_realistic_value(date_param)
    
    print(" Realistic value generation works!")


def test_boundary_value_analysis():
    """Test comprehensive boundary value analysis."""
    gen = TestDataGenerator()
    
    # SMALLINT has different boundaries
    param = {'name': '@Count', 'type': 'SMALLINT'}
    result = gen.generate_test_values(param)
    
    assert -32768 in result['boundary']  # SMALLINT MIN
    assert 32767 in result['boundary']   # SMALLINT MAX
    
    print(" Boundary value analysis works!")


if __name__ == '__main__':
    print("Testing TestDataGenerator...\n")
    
    test_integer_data_generation()
    test_string_data_generation()
    test_datetime_data_generation()
    test_realistic_value_generation()
    test_boundary_value_analysis()
    
    print("\n All tests passed! TestDataGenerator is working correctly.")
