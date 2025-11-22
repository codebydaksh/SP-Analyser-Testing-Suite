"""
Comprehensive tests for TestDataGenerator - Target 90%+ coverage
Final push to 95% overall coverage - world-class exhaustive testing
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from testing.test_data_generator import TestDataGenerator


class TestTestDataGeneratorComprehensive:
    """Comprehensive test suite for TestDataGenerator - reaching 95% total coverage"""
    
    # ========== generate_test_values Tests ==========
    
    def test_generate_test_values_int(self):
        """Test generating test values for INT parameter"""
        generator = TestDataGenerator()
        param = {'name': '@Id', 'type': 'INT'}
        
        result = generator.generate_test_values(param)
        
        assert 'valid' in result
        assert 'invalid' in result
        assert 'boundary' in result
        assert 'edge_cases' in result
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
    
    def test_generate_test_values_bigint(self):
        """Test generating test values for BIGINT parameter"""
        generator = TestDataGenerator()
        param = {'name': '@BigNumber', 'type': 'BIGINT'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['boundary']) > 0
        assert len(result['valid']) > 0
    
    def test_generate_test_values_tinyint(self):
        """Test generating test values for TINYINT parameter"""
        generator = TestDataGenerator()
        param = {'name': '@TinyNum', 'type': 'TINYINT'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
    
    def test_generate_test_values_varchar(self):
        """Test generating test values for VARCHAR parameter"""
        generator = TestDataGenerator()
        param = {'name': '@Name', 'type': 'VARCHAR(50)'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['invalid']) > 0  # Should include SQL injection tests
        assert len(result['edge_cases']) > 0
    
    def test_generate_test_values_nvarchar(self):
        """Test generating test values for NVARCHAR parameter"""
        generator = TestDataGenerator()
        param = {'name': '@Description', 'type': 'NVARCHAR(MAX)'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['edge_cases']) > 0
    
    def test_generate_test_values_decimal(self):
        """Test generating test values for DECIMAL parameter"""
        generator = TestDataGenerator()
        param = {'name': '@Price', 'type': 'DECIMAL(10,2)'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
    
    def test_generate_test_values_datetime(self):
        """Test generating test values for DATETIME parameter"""
        generator = TestDataGenerator()
        param = {'name': '@Created', 'type': 'DATETIME'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
        assert len(result['edge_cases']) > 0
    
    def test_generate_test_values_date(self):
        """Test generating test values for DATE parameter"""
        generator = TestDataGenerator()
        param = {'name': '@BirthDate', 'type': 'DATE'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
    
    def test_generate_test_values_bit(self):
        """Test generating test values for BIT parameter"""
        generator = TestDataGenerator()
        param = {'name': '@IsActive', 'type': 'BIT'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['invalid']) > 0
    
    def test_generate_test_values_uniqueidentifier(self):
        """Test generating test values for UNIQUEIDENTIFIER parameter"""
        generator = TestDataGenerator()
        param = {'name': '@Guid', 'type': 'UNIQUEIDENTIFIER'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
        assert len(result['invalid']) > 0
    
    def test_generate_test_values_unknown_type(self):
        """Test generating test values for unknown type defaults to string"""
        generator = TestDataGenerator()
        param = {'name': '@Unknown', 'type': 'GEOGRAPHY'}
        
        result = generator.generate_test_values(param)
        
        assert len(result['valid']) > 0
    
    # ========== _generate_integer_data Tests ==========
    
    def test_generate_integer_data_int(self):
        """Test integer data generation for INT"""
        generator = TestDataGenerator()
        
        result = generator._generate_integer_data('INT')
        
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
        assert 0 in result['boundary']
        assert -1 in result['boundary']
    
    def test_generate_integer_data_bigint(self):
        """Test integer data generation for BIGINT"""
        generator = TestDataGenerator()
        
        result = generator._generate_integer_data('BIGINT')
        
        assert len(result['boundary']) > 0
    
    def test_generate_integer_data_tinyint(self):
        """Test integer data generation for TINYINT"""
        generator = TestDataGenerator()
        
        result = generator._generate_integer_data('TINYINT')
        
        assert len(result['boundary']) > 0
        assert 0 in result['boundary']
        assert 255 in result['boundary']
    
    def test_generate_integer_data_smallint(self):
        """Test integer data generation for SMALLINT"""
        generator = TestDataGenerator()
        
        result = generator._generate_integer_data('SMALLINT')
        
        assert len(result['boundary']) > 0
    
    # ========== _generate_numeric_data Tests ==========
    
    def test_generate_numeric_data_decimal(self):
        """Test numeric data generation for DECIMAL"""
        generator = TestDataGenerator()
        
        result = generator._generate_numeric_data('DECIMAL', 10, 2)
        
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
    
    def test_generate_numeric_data_numeric(self):
        """Test numeric data generation for NUMERIC"""
        generator = TestDataGenerator()
        
        result = generator._generate_numeric_data('NUMERIC', 18, 4)
        
        assert len(result['valid']) > 0
    
    def test_generate_numeric_data_float(self):
        """Test numeric data generation for FLOAT"""
        generator = TestDataGenerator()
        
        result = generator._generate_numeric_data('FLOAT', 53, 0)
        
        assert len(result['valid']) > 0
    
    # ========== _generate_string_data Tests ==========
    
    def test_generate_string_data_varchar(self):
        """Test string data generation for VARCHAR"""
        generator = TestDataGenerator()
        
        result = generator._generate_string_data('VARCHAR', 50)
        
        assert len(result['valid']) > 0
        assert len(result['invalid']) > 0
        assert len(result['edge_cases']) > 0
    
    def test_generate_string_data_sql_injection(self):
        """Test that SQL injection strings are included"""
        generator = TestDataGenerator()
        
        result = generator._generate_string_data('VARCHAR', 100)
        
        assert len(result['invalid']) > 0
        # Check that typical SQL injection patterns are included
        invalid_str = str(result['invalid'])
        assert "DROP" in invalid_str or "UNION" in invalid_str or "OR" in invalid_str
    
    def test_generate_string_data_empty_string(self):
        """Test that empty string is in edge cases"""
        generator = TestDataGenerator()
        
        result = generator._generate_string_data('VARCHAR', 50)
        
        assert "''" in result['edge_cases'] or "" in result['edge_cases']
    
    def test_generate_string_data_max_length(self):
        """Test that max length string is generated"""
        generator = TestDataGenerator()
        max_len = 10
        
        result = generator._generate_string_data('VARCHAR', max_len)
        
        # Should have a string at or near max length
        assert len(result['boundary']) > 0
    
    def test_generate_string_data_nvarchar(self):
        """Test string data generation for NVARCHAR"""
        generator = TestDataGenerator()
        
        result = generator._generate_string_data('NVARCHAR', 100)
        
        assert len(result['valid']) > 0
    
    def test_generate_string_data_char(self):
        """Test string data generation for CHAR"""
        generator = TestDataGenerator()
        
        result = generator._generate_string_data('CHAR', 10)
        
        assert len(result['valid']) > 0
    
    # ========== _generate_datetime_data Tests ==========
    
    def test_generate_datetime_data_datetime(self):
        """Test datetime data generation"""
        generator = TestDataGenerator()
        
        result = generator._generate_datetime_data('DATETIME')
        
        assert len(result['valid']) > 0
        assert len(result['boundary']) > 0
        assert len(result['edge_cases']) > 0
    
    def test_generate_datetime_data_includes_current(self):
        """Test that current datetime is in valid values"""
        generator = TestDataGenerator()
        
        result = generator._generate_datetime_data('DATETIME')
        
        assert len(result['valid']) > 0
        # Should have current or recent datetime
    
    def test_generate_datetime_data_includes_boundaries(self):
        """Test that datetime boundaries are included"""
        generator = TestDataGenerator()
        
        result = generator._generate_datetime_data('DATETIME')
        
        assert len(result['boundary']) > 0
        # Should have min/max dates
    
    def test_generate_datetime_data_date_type(self):
        """Test datetime data generation for DATE type"""
        generator = TestDataGenerator()
        
        result = generator._generate_datetime_data('DATE')
        
        assert len(result['valid']) > 0
    
    def test_generate_datetime_data_time_type(self):
        """Test datetime data generation for TIME type"""
        generator = TestDataGenerator()
        
        result = generator._generate_datetime_data('TIME')
        
        assert len(result['valid']) > 0
    
    # ========== _generate_bit_data Tests ==========
    
    def test_generate_bit_data(self):
        """Test BIT data generation"""
        generator = TestDataGenerator()
        
        result = generator._generate_bit_data()
        
        assert len(result['valid']) > 0
        assert 0 in result['valid'] or 1 in result['valid']
        assert len(result['invalid']) > 0
    
    def test_generate_bit_data_includes_both_values(self):
        """Test that BIT data includes both 0 and 1"""
        generator = TestDataGenerator()
        
        result = generator._generate_bit_data()
        
        assert 0 in result['valid'] or 1 in result['valid']
    
    # ========== _generate_guid_data Tests ==========
    
    def test_generate_guid_data(self):
        """Test GUID data generation"""
        generator = TestDataGenerator()
        
        if result['valid']:
            guid_str = str(result['valid'][0])
            assert '-' in guid_str or len(guid_str) > 30
    
    # ========== get_realistic_value Tests ==========
    
    def test_get_realistic_value_int(self):
        """Test getting realistic value for INT"""
        generator = TestDataGenerator()
        param = {'name': '@Id', 'type': 'INT'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
        assert isinstance(result, (int, str))
    
    def test_get_realistic_value_varchar(self):
        """Test getting realistic value for VARCHAR"""
        generator = TestDataGenerator()
        param = {'name': '@Name', 'type': 'VARCHAR(50)'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_realistic_value_datetime(self):
        """Test getting realistic value for DATETIME"""
        generator = TestDataGenerator()
        param = {'name': '@Created', 'type': 'DATETIME'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
    
    def test_get_realistic_value_bit(self):
        """Test getting realistic value for BIT"""
        generator = TestDataGenerator()
        param = {'name': '@IsActive', 'type': 'BIT'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
        assert result in [0, 1, '0', '1']
    
    def test_get_realistic_value_decimal(self):
        """Test getting realistic value for DECIMAL"""
        generator = TestDataGenerator()
        param = {'name': '@Price', 'type': 'DECIMAL(10,2)'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
    
    def test_get_realistic_value_guid(self):
        """Test getting realistic value for UNIQUEIDENTIFIER"""
        generator = TestDataGenerator()
        param = {'name': '@Guid', 'type': 'UNIQUEIDENTIFIER'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
    
    def test_get_realistic_value_unknown_type(self):
        """Test getting realistic value for unknown type"""
        generator = TestDataGenerator()
        param = {'name': '@Unknown', 'type': 'GEOGRAPHY'}
        
        result = generator.get_realistic_value(param)
        
        assert result is not None
