"""
Table Mocker for tSQLt Unit Tests

Automatically generates:
- tSQLt.FakeTable calls for all dependencies
- Fixture data insertion scripts
- Setup/Teardown methods
"""
from typing import Dict, List, Any
import re


class TableMocker:
    """Generate tSQLt table mocking code automatically."""
    
    def __init__(self):
        pass
    
    def extract_table_dependencies(self, sp_analysis: Dict[str, Any]) -> List[str]:
        """
        Extract all table dependencies from SP analysis.
        
        Args:
            sp_analysis: Result from SPAnalyzer containing 'tables' key
            
        Returns:
            List of table names that need to be mocked
        """
        tables = sp_analysis.get('tables', [])
        
        # Filter out temp tables (they don't need mocking)
        real_tables = [t for t in tables if not t.startswith('#')]
        
        return sorted(list(set(real_tables)))
    
    def generate_fake_table_calls(self, tables: List[str]) -> List[str]:
        """
        Generate tSQLt.FakeTable calls for each table.
        
        Args:
            tables: List of table names to mock
            
        Returns:
            List of SQL statements for faking tables
        """
        fake_calls = []
        
        for table in tables:
            # Handle schema.table format
            if '.' in table:
                fake_calls.append(f"    EXEC tSQLt.FakeTable '{table}';")
            else:
                # Assume dbo schema if not specified
                fake_calls.append(f"    EXEC tSQLt.FakeTable 'dbo.{table}';")
        
        return fake_calls
    
    def create_fixture_data(self, tables: List[str], test_scenario: str = 'basic') -> List[str]:
        """
        Generate fixture data insertion scripts for tables.
        
        Args:
            tables: List of table names
            test_scenario: Type of test data ('basic', 'edge_case', 'empty')
            
        Returns:
            List of INSERT statements
        """
        fixture_statements = []
        
        if test_scenario == 'empty':
            # No data - testing empty table scenarios
            fixture_statements.append("    -- Empty table scenario: No test data inserted")
            return fixture_statements
        
        for table in tables:
            table_name = table if '.' in table else f'dbo.{table}'
            
            if test_scenario == 'basic':
                # Basic test data
                fixture_statements.append(f"    -- Insert test data for {table_name}")
                fixture_statements.append(f"    INSERT INTO {table_name} (Id) VALUES (1);")
                fixture_statements.append(f"    INSERT INTO {table_name} (Id) VALUES (2);")
            elif test_scenario == 'edge_case':
                # Edge case data
                fixture_statements.append(f"    -- Insert edge case data for {table_name}")
                fixture_statements.append(f"    INSERT INTO {table_name} (Id) VALUES (NULL);  -- NULL ID")
                fixture_statements.append(f"    INSERT INTO {table_name} (Id) VALUES (-1);   -- Negative ID")
                fixture_statements.append(f"    INSERT INTO {table_name} (Id) VALUES (999999);  -- Very large ID")
        
        return fixture_statements
    
    def generate_setup_teardown(self, test_class: str, tables: List[str], 
                               test_scenario: str = 'basic') -> str:
        """
        Generate complete setup and teardown methods for test class.
        
        Args:
            test_class: Name of the tSQLt test class
            tables: List of tables to mock
            test_scenario: Type of test data to create
            
        Returns:
            SQL code for setup and teardown methods
        """
        setup_code = []
        
        # Setup method
        setup_code.append(f"CREATE PROCEDURE [{test_class}].[SetUp]")
        setup_code.append("AS")
        setup_code.append("BEGIN")
        setup_code.append("    -- Fake all dependent tables")
        
        # Add FakeTable calls
        fake_calls = self.generate_fake_table_calls(tables)
        setup_code.extend(fake_calls)
        
        setup_code.append("")
        setup_code.append("    -- Insert test fixture data")
        
        # Add fixture data
        fixture_data = self.create_fixture_data(tables, test_scenario)
        setup_code.extend(fixture_data)
        
        setup_code.append("END;")
        setup_code.append("GO\n")
        
        # TearDown method (optional - tSQLt auto-rolls back, but good practice)
        setup_code.append(f"CREATE PROCEDURE [{test_class}].[TearDown]")
        setup_code.append("AS")
        setup_code.append("BEGIN")
        setup_code.append("    -- tSQLt automatically rolls back transactions")
        setup_code.append("    -- This method is here for explicit cleanup if needed")
        setup_code.append("END;")
        setup_code.append("GO\n")
        
        return "\n".join(setup_code)
    
    def generate_complete_test_with_mocks(self, proc_name: str, parameters: List[Dict], 
                                         tables: List[str]) -> str:
        """
        Generate a complete test including mocks.
        
        Args:
            proc_name: Stored procedure name
            parameters: List of parameter dicts
            tables: List of tables to mock
            
        Returns:
            Complete test code with mocking
        """
        clean_proc_name = proc_name.replace('[', '').replace(']', '')
        test_class = f"Test{clean_proc_name.replace('.', '_')}"
        
        # For EXEC statements
        if '.' in clean_proc_name:
            schema, name = clean_proc_name.split('.', 1)
            exec_proc_name = f"[{schema}].[{name}]"
        else:
            exec_proc_name = f"[{clean_proc_name}]"
        
        test_code = []
        
        # Header
        test_code.append("-- ===============================================")
        test_code.append(f"-- tSQLt Tests with Table Mocking for {clean_proc_name}")
        test_code.append("-- ===============================================\n")
        
        # Create test class
        test_code.append(f"EXEC tSQLt.NewTestClass '{test_class}';")
        test_code.append("GO\n")
        
        # Setup/TearDown
        test_code.append(self.generate_setup_teardown(test_class, tables, 'basic'))
        
        # Sample test
        test_code.append(f"CREATE PROCEDURE [{test_class}].[test_WithMockedTables_ExecutesSuccessfully]")
        test_code.append("AS")
        test_code.append("BEGIN")
        test_code.append("    -- Arrange: Tables are already faked in SetUp")
        
        if parameters:
            for p in parameters:
                # Simplified default value
                default_val = "'test'" if 'VARCHAR' in p.get('type', '').upper() else "1"
                test_code.append(f"    DECLARE {p['name']} {p['type']} = {default_val};")
        
        test_code.append("    DECLARE @ReturnValue INT;")
        test_code.append("")
        test_code.append("    -- Act: Execute procedure with mocked tables")
        
        if parameters:
            param_list = ", ".join([f"{p['name']} = {p['name']}" for p in parameters])
            test_code.append(f"    EXEC @ReturnValue = {exec_proc_name} {param_list};")
        else:
            test_code.append(f"    EXEC @ReturnValue = {exec_proc_name};")
        
        test_code.append("")
        test_code.append("    -- Assert: Verify success")
        test_code.append("    EXEC tSQLt.AssertEquals")
        test_code.append("        @Expected = 0,")
        test_code.append("        @Actual = @ReturnValue,")
        test_code.append("        @Message = 'Procedure should execute successfully with mocked tables';")
        test_code.append("END;")
        test_code.append("GO\n")
        
        return "\n".join(test_code)
