"""
Comprehensive tests for TableMocker - Target 90%+ coverage
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from testing.table_mocker import TableMocker


class TestTableMocker:
    """Test suite for TableMocker functionality"""
    
    def test_extract_dependencies_basic(self):
        """Test basic table dependency extraction"""
        mocker = TableMocker()
        
        sp_analysis = {
            'tables': ['Users', 'Orders', 'Products']
        }
        
        result = mocker.extract_table_dependencies(sp_analysis)
        
        assert len(result) == 3
        assert 'Users' in result
        assert 'Orders' in result
    
    def test_extract_dependencies_filters_temp_tables(self):
        """Test that temp tables are filtered out"""
        mocker = TableMocker()
        
        sp_analysis = {
            'tables': ['Users', '#TempTable', '##GlobalTemp', 'Orders']
        }
        
        result = mocker.extract_table_dependencies(sp_analysis)
        
        assert len(result) == 2
        assert 'Users' in result
        assert 'Orders' in result
        assert '#TempTable' not in result
    
    def test_generate_fake_table_calls_with_schema(self):
        """Test generating FakeTable calls with schema"""
        mocker = TableMocker()
        
        tables = ['dbo.Users', 'sales.Orders']
        result = mocker.generate_fake_table_calls(tables)
        
        assert len(result) == 2
        assert "EXEC tSQLt.FakeTable 'dbo.Users';" in result[0]
        assert "EXEC tSQLt.FakeTable 'sales.Orders';" in result[1]
    
    def test_generate_fake_table_calls_without_schema(self):
        """Test generating FakeTable calls without schema"""
        mocker = TableMocker()
        
        tables = ['Users', 'Orders']
        result = mocker.generate_fake_table_calls(tables)
        
        assert len(result) == 2
        assert "EXEC tSQLt.FakeTable 'dbo.Users';" in result[0]
        assert "EXEC tSQLt.FakeTable 'dbo.Orders';" in result[1]
    
    def test_create_fixture_data_basic(self):
        """Test basic fixture data generation"""
        mocker = TableMocker()
        
        tables = ['Users']
        result = mocker.create_fixture_data(tables, 'basic')
        
        assert len(result) > 0
        assert any('INSERT INTO' in stmt for stmt in result)
    
    def test_create_fixture_data_empty_scenario(self):
        """Test empty table scenario"""
        mocker = TableMocker()
        
        tables = ['Users']
        result = mocker.create_fixture_data(tables, 'empty')
        
        assert len(result) > 0
        assert 'Empty table scenario' in result[0]
    
    def test_create_fixture_data_edge_case(self):
        """Test edge case data generation"""
        mocker = TableMocker()
        
        tables = ['Users']
        result = mocker.create_fixture_data(tables, 'edge_case')
        
        assert len(result) > 0
        assert any('NULL' in stmt for stmt in result)
        assert any('-1' in stmt for stmt in result)
    
    def test_generate_setup_teardown(self):
        """Test setup/teardown generation"""
        mocker = TableMocker()
        
        result = mocker.generate_setup_teardown('TestClass', ['Users', 'Orders'])
        
        assert 'CREATE PROCEDURE [TestClass].[SetUp]' in result
        assert 'CREATE PROCEDURE [TestClass].[TearDown]' in result
        assert 'tSQLt.FakeTable' in result
    
    def test_generate_complete_test(self):
        """Test complete test generation"""
        mocker = TableMocker()
        
        parameters = [
            {'name': '@UserId', 'type': 'INT'},
            {'name': '@Name', 'type': 'VARCHAR(100)'}
        ]
        
        result = mocker.generate_complete_test_with_mocks(
            'dbo.ProcessUser',
            parameters,
            ['Users', 'Orders']
        )
        
        assert 'tSQLt.NewTestClass' in result
        assert 'SetUp' in result
        assert 'TearDown' in result
        assert 'ProcessUser' in result
    
    def test_no_tables(self):
        """Test handling of no tables"""
        mocker = TableMocker()
        
        sp_analysis = {'tables': []}
        result = mocker.extract_table_dependencies(sp_analysis)
        
        assert len(result) == 0
    
    def test_duplicate_tables_deduplicated(self):
        """Test that duplicate tables are deduplicated"""
        mocker = TableMocker()
        
        sp_analysis = {'tables': ['Users', 'Users', 'Orders', 'Users']}
        result = mocker.extract_table_dependencies(sp_analysis)
        
        assert len(result) == 2
        assert result.count('Users') == 1
