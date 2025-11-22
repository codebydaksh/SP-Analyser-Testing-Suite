"""
Comprehensive tests for SPTestGenerator - Target 90%+ coverage
World-class exhaustive testing - continuing to 95% overall coverage
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyzer.test_generator import SPTestGenerator
from parser.sp_parser import SPParser
from sqlglot import exp


class TestSPTestGeneratorComprehensive:
    """Comprehensive test suite for SPTestGenerator - world-class coverage"""
    
    # ========== Initialization Tests ==========
    
    def test_init_basic_mode(self):
        """Test initialization without enhanced features"""
        generator = SPTestGenerator(use_enhanced_features=False)
        assert generator.use_enhanced_features == False
        assert generator.test_data_gen is None
        assert generator.table_mocker is None
    
    def test_init_enhanced_mode(self):
        """Test initialization with enhanced features"""
        generator = SPTestGenerator(use_enhanced_features=True)
        assert generator.use_enhanced_features == True
        assert generator.test_data_gen is not None
        assert generator.table_mocker is not None
    
    def test_init_default_mode(self):
        """Test initialization uses basic mode by default"""
        generator = SPTestGenerator()
        assert generator.use_enhanced_features == False
    
    # ========== extract_parameters Tests ==========
    
    def test_extract_parameters_no_params(self):
        """Test extracting parameters from SP with no parameters"""
        parser = SPParser()
        sql = """
        CREATE PROCEDURE dbo.NoParams
        AS
        BEGIN
            SELECT 1;
        END
        """
        ast = parser.parse(sql)
        generator = SPTestGenerator()
        params = generator.extract_parameters(ast)
        assert isinstance(params, list)
        assert len(params) == 0
    
    def test_extract_parameters_with_params(self):
        """Test extracting parameters from SP with parameters"""
        generator = SPTestGenerator()
        # Create mock AST with parameters
        mock_create = Mock(spec=exp.Create)
        mock_param1 = Mock()
        mock_param1.this = "@UserId"
        mock_param1.args = {'kind': 'INT', 'default': None}
        mock_create.args = {'params': [mock_param1]}
        
        params = generator.extract_parameters(mock_create)
        
        assert len(params) == 1
        assert params[0]['name'] == "@UserId"
        assert 'INT' in params[0]['type']
    
    def test_extract_parameters_list_of_nodes(self):
        """Test extracting parameters when AST is a list"""
        generator = SPTestGenerator()
        mock_create = Mock(spec=exp.Create)
        mock_create.args = {'params': []}
        
        params = generator.extract_parameters([mock_create])
        
        assert isinstance(params, list)
    
    def test_extract_parameters_no_create_node(self):
        """Test extracting parameters when no CREATE node exists"""
        generator = SPTestGenerator()
        mock_node = Mock(spec=exp.Select)  # Not a CREATE node
        
        params = generator.extract_parameters([mock_node])
        
        assert params == []
    
    def test_extract_parameters_empty_params_list(self):
        """Test extracting when params list exists but is empty"""
        generator = SPTestGenerator()
        mock_create = Mock(spec=exp.Create)
        mock_create.args = {'params': None}
        
        params = generator.extract_parameters(mock_create)
        
        assert isinstance(params, list)
    
    # ========== generate_tsqlt_tests Tests ==========
    
    def test_generate_tsqlt_basic(self):
        """Test basic tSQLt test generation"""
        generator = SPTestGenerator()
        params = [{'name': '@UserId', 'type': 'INT', 'default': None}]
        
        result = generator.generate_tsqlt_tests('dbo.GetUser', params)
        
        assert 'tSQLt.NewTestClass' in result
        assert 'Test' in result  # Should have test class name
        assert 'test_BasicExecution' in result
        assert 'EXEC dbo.GetUser' in result
    
    def test_generate_tsqlt_no_params(self):
        """Test tSQLt generation for SP with no parameters"""
        generator = SPTestGenerator()
        
        result = generator.generate_tsqlt_tests('dbo.SimpleProc', [])
        
        assert 'tSQLt.NewTestClass' in result
        assert 'EXEC dbo.SimpleProc' in result
    
    def test_generate_tsqlt_multiple_params(self):
        """Test tSQLt generation with multiple parameters"""
        generator = SPTestGenerator()
        params = [
            {'name': '@UserId', 'type': 'INT', 'default': None},
            {'name': '@UserName', 'type': 'VARCHAR(50)', 'default': "'guest'"},
            {'name': '@IsActive', 'type': 'BIT', 'default': '1'}
        ]
        
        result = generator.generate_tsqlt_tests('dbo.UpdateUser', params)
        
        assert 'EXEC dbo.UpdateUser' in result
        assert 'test_BasicExecution' in result
    
    def test_generate_tsqlt_null_test_included(self):
        """Test that NULL parameter test is generated when appropriate"""
        generator = SPTestGenerator()
        params = [{'name': '@OptionalParam', 'type': 'INT', 'default': None}]
        
        result = generator.generate_tsqlt_tests('dbo.TestProc', params)
        
        assert 'test_NullParameters' in result
        assert 'NULL' in result
    
    def test_generate_tsqlt_enhanced_mode(self):
        """Test tSQLt generation in enhanced mode"""
        generator = SPTestGenerator(use_enhanced_features=True)
        params = [{'name': '@Input', 'type': 'VARCHAR(100)', 'default': None}]
        tables = ['Users', 'Orders']
        
        result = generator.generate_tsqlt_tests('dbo.ProcessData', params, tables)
        
        assert 'SetUp' in result
        assert 'test_BoundaryValues' in result
        assert 'test_SQLInjectionProtection' in result
    
    def test_generate_tsqlt_with_table_mocking(self):
        """Test tSQLt generation includes table mocking setup"""
        generator = SPTestGenerator(use_enhanced_features=True)
        params = []
        tables = ['dbo.Customers', 'dbo.Products']
        
        result = generator.generate_tsqlt_tests('dbo.GetSales', params, tables)
        
        assert 'SetUp' in result
        assert 'FakeTables' in result or 'Fake' in result
    
    def test_generate_tsqlt_boundary_value_tests(self):
        """Test that boundary value tests are generated in enhanced mode"""
        generator = SPTestGenerator(use_enhanced_features=True)
        params = [
            {'name': '@Count', 'type': 'INT', 'default': None},
            {'name': '@Price', 'type': 'DECIMAL(10,2)', 'default': None}
        ]
        
        result = generator.generate_tsqlt_tests('dbo.Calculate', params)
        
        assert 'test_BoundaryValues' in result
        assert 'boundary' in result.lower()
    
    def test_generate_tsqlt_sql_injection_test(self):
        """Test that SQL injection tests are generated for VARCHAR params"""
        generator = SPTestGenerator(use_enhanced_features=True)
        params = [
            {'name': '@SearchTerm', 'type': 'VARCHAR(255)', 'default': None},
            {'name': '@Category', 'type': 'NVARCHAR(50)', 'default': None}
        ]
        
        result = generator.generate_tsqlt_tests('dbo.Search', params)
        
        assert 'test_SQLInjectionProtection' in result
        assert 'injection' in result.lower()
    
    # ========== generate_ssdt_tests Tests ==========
    
    def test_generate_ssdt_basic(self):
        """Test basic SSDT test generation"""
        generator = SPTestGenerator()
        params = [{'name': '@UserId', 'type': 'INT', 'default': None}]
        
        result = generator.generate_ssdt_tests('dbo.GetUser', params)
        
        assert 'SSDT Test Suite' in result
        assert 'EXEC' in result
        assert 'dbo.GetUser' in result
    
    def test_generate_ssdt_no_params(self):
        """Test SSDT generation with no parameters"""
        generator = SPTestGenerator()
        
        result = generator.generate_ssdt_tests('dbo.SimpleProc', [])
        
        assert 'SSDT Test Suite' in result
        assert 'EXEC' in result
    
    def test_generate_ssdt_multiple_params(self):
        """Test SSDT generation with multiple parameters"""
        generator = SPTestGenerator()
        params = [
            {'name': '@Id', 'type': 'INT', 'default': None},
            {'name': '@Name', 'type': 'VARCHAR(100)', 'default': None},
            {'name': '@Active', 'type': 'BIT', 'default': '1'}
        ]
        
        result = generator.generate_ssdt_tests('dbo.UpdateRecord', params)
        
        assert 'EXEC' in result
        assert '@result' in result
        assert 'THROW' in result
    
    def test_generate_ssdt_includes_error_handling(self):
        """Test that SSDT tests include error handling"""
        generator = SPTestGenerator()
        params = [{'name': '@Input', 'type': 'INT', 'default': None}]
        
        result = generator.generate_ssdt_tests('dbo.Process', params)
        
        assert 'THROW' in result
        assert 'IF @result' in result or '@result' in result
    
    def test_generate_ssdt_includes_pass_message(self):
        """Test that SSDT tests include PASS message"""
        generator = SPTestGenerator()
        params = []
        
        result = generator.generate_ssdt_tests('dbo.Test', params)
        
        assert 'PASS' in result
        assert 'PRINT' in result
    
    # ========== _get_default_value Tests ==========
    
    def test_get_default_value_int(self):
        """Test default value for INT type"""
        generator = SPTestGenerator()
        param = {'type': 'INT', 'name': '@Count'}
        
        result = generator._get_default_value(param)
        
        assert result == "1"
    
    def test_get_default_value_bigint(self):
        """Test default value for BIGINT type"""
        generator = SPTestGenerator()
        param = {'type': 'BIGINT', 'name': '@LargeNum'}
        
        result = generator._get_default_value(param)
        
        assert result == "1"
    
    def test_get_default_value_numeric(self):
        """Test default value for NUMERIC type"""
        generator = SPTestGenerator()
        param = {'type': 'NUMERIC(10,2)', 'name': '@Amount'}
        
        result = generator._get_default_value(param)
        
        assert result == "1"
    
    def test_get_default_value_decimal(self):
        """Test default value for DECIMAL type"""
        generator = SPTestGenerator()
        param = {'type': 'DECIMAL(18,4)', 'name': '@Price'}
        
        result = generator._get_default_value(param)
        
        assert result == "1"
    
    def test_get_default_value_varchar(self):
        """Test default value for VARCHAR type"""
        generator = SPTestGenerator()
        param = {'type': 'VARCHAR(50)', 'name': '@Name'}
        
        result = generator._get_default_value(param)
        
        assert result == "'test'"
    
    def test_get_default_value_nvarchar(self):
        """Test default value for NVARCHAR type"""
        generator = SPTestGenerator()
        param = {'type': 'NVARCHAR(MAX)', 'name': '@Description'}
        
        result = generator._get_default_value(param)
        
        assert result == "'test'"
    
    def test_get_default_value_char(self):
        """Test default value for CHAR type"""
        generator = SPTestGenerator()
        param = {'type': 'CHAR(10)', 'name': '@Code'}
        
        result = generator._get_default_value(param)
        
        assert result == "'test'"
    
    def test_get_default_value_text(self):
        """Test default value for TEXT type"""
        generator = SPTestGenerator()
        param = {'type': 'TEXT', 'name': '@LongText'}
        
        result = generator._get_default_value(param)
        
        assert result == "'test'"
    
    def test_get_default_value_date(self):
        """Test default value for DATE type"""
        generator = SPTestGenerator()
        param = {'type': 'DATE', 'name': '@BirthDate'}
        
        result = generator._get_default_value(param)
        
        assert result == "'2024-01-01'"
    
    def test_get_default_value_datetime(self):
        """Test default value for DATETIME type"""
        generator = SPTestGenerator()
        param = {'type': 'DATETIME', 'name': '@CreatedAt'}
        
        result = generator._get_default_value(param)
        
        assert result == "'2024-01-01'"
    
    def test_get_default_value_time(self):
        """Test default value for TIME type"""
        generator = SPTestGenerator()
        param = {'type': 'TIME', 'name': '@StartTime'}
        
        result = generator._get_default_value(param)
        
        assert result == "'2024-01-01'"
    
    def test_get_default_value_bit(self):
        """Test default value for BIT type"""
        generator = SPTestGenerator()
        param = {'type': 'BIT', 'name': '@IsActive'}
        
        result = generator._get_default_value(param)
        
        assert result == "1"
    
    def test_get_default_value_unknown_type(self):
        """Test default value for unknown/unsupported type"""
        generator = SPTestGenerator()
        param = {'type': 'GEOGRAPHY', 'name': '@Location'}
        
        result = generator._get_default_value(param)
        
        assert result == "'default'"
    
    def test_get_default_value_case_insensitive(self):
        """Test that type matching is case-insensitive"""
        generator = SPTestGenerator()
        param_lower = {'type': 'int', 'name': '@Id'}
        param_mixed = {'type': 'VarChar(50)', 'name': '@Name'}
        
        result_int = generator._get_default_value(param_lower)
        result_varchar = generator._get_default_value(param_mixed)
        
        assert result_int == "1"
        assert result_varchar == "'test'"
