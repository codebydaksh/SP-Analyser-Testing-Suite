"""
Unit Test Generator for T-SQL Stored Procedures
"""
from sqlglot import exp
from typing import List, Dict, Any

class SPTestGenerator:
    """
    Generates unit tests for T-SQL stored procedures.
    Supports tSQLt and SSDT formats.
    """
    def __init__(self):
        pass

    def extract_parameters(self, ast) -> List[Dict[str, Any]]:
        """
        Extract parameters from CREATE PROCEDURE statement.
        Returns list of dicts with 'name', 'type', 'default' keys.
        """
        parameters = []
        
        # Find CREATE statement
        create_node = None
        if isinstance(ast, list):
            for node in ast:
                if isinstance(node, exp.Create):
                    create_node = node
                    break
        elif isinstance(ast, exp.Create):
            create_node = ast
            
        if not create_node:
            return parameters
            
        # Parameters might be in args['params'] or similar
        # sqlglot structure varies; try to find them
        if hasattr(create_node, 'args') and 'params' in create_node.args:
            param_list = create_node.args['params']
            if param_list:
                for param in param_list:
                    param_info = {
                        'name': str(param.this) if hasattr(param, 'this') else str(param),
                        'type': str(param.args.get('kind', 'VARCHAR')) if hasattr(param, 'args') else 'VARCHAR',
                        'default': param.args.get('default') if hasattr(param, 'args') else None
                    }
                    parameters.append(param_info)
                    
        return parameters

    def generate_tsqlt_tests(self, proc_name: str, parameters: List[Dict[str, Any]]) -> str:
        """Generate tSQLt test suite for the given stored procedure."""
        test_class = f"Test{proc_name.replace('.', '_')}"
        
        tests = []
        tests.append(f"EXEC tSQLt.NewTestClass '{test_class}';")
        tests.append("GO\n")
        
        # Test 1: Basic execution
        tests.append(f"CREATE PROCEDURE [{test_class}].[test_BasicExecution]")
        tests.append("AS")
        tests.append("BEGIN")
        tests.append(f"    -- Arrange")
        tests.append(f"    -- Act")
        param_values = ", ".join([self._get_default_value(p) for p in parameters])
        tests.append(f"    EXEC {proc_name} {param_values};")
        tests.append(f"    -- Assert")
        tests.append(f"    -- Add assertions here")
        tests.append("END;")
        tests.append("GO\n")
        
        # Test 2: NULL parameters
        if any(p.get('default') is None for p in parameters):
            tests.append(f"CREATE PROCEDURE [{test_class}].[test_NullParameters]")
            tests.append("AS")
            tests.append("BEGIN")
            tests.append(f"    -- Test with NULL parameters")
            null_params = ", ".join(["NULL" for _ in parameters])
            tests.append(f"    EXEC {proc_name} {null_params};")
            tests.append("END;")
            tests.append("GO\n")
        
        return "\n".join(tests)

    def generate_ssdt_tests(self, proc_name: str, parameters: List[Dict[str, Any]]) -> str:
        """Generate SSDT-compatible test suite."""
        test_name = f"{proc_name.replace('.', '_')}_Tests"
        
        tests = []
        tests.append(f"-- SSDT Test Suite for {proc_name}")
        tests.append(f"-- Run with: SqlCmd or SSDT Test Runner\n")
        
        tests.append(f"-- Test: Basic Execution")
        tests.append(f"DECLARE @result INT;")
        param_values = ", ".join([self._get_default_value(p) for p in parameters])
        tests.append(f"EXEC @result = {proc_name} {param_values};")
        tests.append(f"IF @result <> 0 THROW 50000, 'Test failed: Basic execution', 1;")
        tests.append(f"PRINT 'PASS: Basic execution';\n")
        
        return "\n".join(tests)

    def _get_default_value(self, param: Dict[str, Any]) -> str:
        """Get a default test value for a parameter based on its type."""
        param_type = param['type'].upper()
        
        if 'INT' in param_type or 'NUMERIC' in param_type or 'DECIMAL' in param_type:
            return "1"
        elif 'VARCHAR' in param_type or 'CHAR' in param_type or 'TEXT' in param_type:
            return "'test'"
        elif 'DATE' in param_type or 'TIME' in param_type:
            return "'2024-01-01'"
        elif 'BIT' in param_type:
            return "1"
        else:
            return "'default'"
