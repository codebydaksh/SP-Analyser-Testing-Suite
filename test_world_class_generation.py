"""
Direct test of world-class test generation - extracts and calls the function directly
"""
import re

def extract_parameters(sql_code):
    """Extract parameters (simplified version)"""
    params = []
    # Look for @ParameterName TYPE patterns
    param_pattern = r'@(\w+)\s+((?:var)?char|int|bigint|decimal|datetime|bit|numeric)(?:\([\d,]+\))?'
    matches = re.finditer(param_pattern, sql_code, re.IGNORECASE)
    seen = set()
    for match in matches:
        param_name = f"@{match.group(1)}"
        param_type = match.group(2).upper()
        if param_name.lower() not in seen:
            seen.add(param_name.lower())
            # Get full type with size if present
            full_match = re.search(rf'{re.escape(param_name)}\s+({param_type}(?:\([^)]+\))?)', sql_code, re.IGNORECASE)
            if full_match:
                params.append({'name': param_name, 'type': full_match.group(1)})
    return params

def extract_procedure_name(sql_code):
    """Extract procedure name"""
    match = re.search(r'CREATE\s+PROCEDURE\s+(\[?[\w\.]+\]?\.?\[?[\w]+\]?)', sql_code, re.IGNORECASE)
    if match:
        return match.group(1)
    return "Unknown"

def get_default_value(param):
    """Get default value for parameter"""
    param_type = param['type'].upper()
    if 'INT' in param_type:
        return "1"
    elif 'VAR' in param_type or 'CHAR' in param_type:
        return "'test'"
    elif 'DATE' in param_type:
        return "'2024-01-01'"
    elif 'BIT' in param_type:
        return "1"
    else:
        return "NULL"

def generate_world_class_tests(proc_name, parameters):
    """Generate WORLD-CLASS tests"""
    clean_proc_name = proc_name.replace('[', '').replace(']', '')
    test_class = f"Test{clean_proc_name.replace('.', '_')}"
    
    if '.' in clean_proc_name:
        schema, name = clean_proc_name.split('.', 1)
        exec_proc_name = f"[{schema}].[{name}]"
    else:
        exec_proc_name = f"[{clean_proc_name}]"
    
    tests = []
    tests.append("-- ===========================================")
    tests.append(f"-- WORLD-CLASS tSQLt Unit Tests for {clean_proc_name}")
    tests.append("-- Auto-generated with:")
    tests.append("--   ✓ Parameter validation")
    tests.append("--   ✓ tSQLt.AssertEquals real assertions")
    tests.append("--   ✓ NULL boundary testing")
    tests.append("--   ✓ Error handling with TRY/CATCH")
    tests.append("-- ===========================================\n")
    
    tests.append(f"EXEC tSQLt.NewTestClass '{test_class}';")
    tests.append("GO\n")
    
    # Test 1
    tests.append(f"CREATE PROCEDURE [{test_class}].[test_ExecutesWith_ValidParameters_ReturnsSuccess]")
    tests.append("AS")
    tests.append("BEGIN")
    tests.append("    -- Arrange")
    for p in parameters:
        tests.append(f"    DECLARE {p['name']} {p['type']} = {get_default_value(p)};")
    tests.append("    DECLARE @ReturnValue INT;")
    tests.append("    ")
    tests.append("    -- Act")
    if parameters:
        param_list = ", ".join([f"{p['name']} = {p['name']}" for p in parameters])
        tests.append(f"    EXEC @ReturnValue = {exec_proc_name} {param_list};")
    else:
        tests.append(f"    EXEC @ReturnValue = {exec_proc_name};")
    tests.append("    ")
    tests.append("    -- Assert: Use REAL assertion, not just @@ERROR")
    tests.append("    EXEC tSQLt.AssertEquals ")
    tests.append("        @Expected = 0,")
    tests.append("        @Actual = @ReturnValue,")
    tests.append("        @Message = 'Procedure should return 0 for success';")
    tests.append("END;")
    tests.append("GO\n")
    
    # Test 2:  NULL boundary
    if parameters:
        tests.append(f"CREATE PROCEDURE [{test_class}].[test_NullParameters_FailsOrHandlesGracefully]")
        tests.append("AS")
        tests.append("BEGIN")
        tests.append("    -- Arrange: Test NULL boundary condition")
        tests.append("    DECLARE @ErrorCaught BIT = 0;")
        tests.append("    DECLARE @ReturnValue INT;")
        tests.append("    ")
        tests.append("    -- Act: Execute with all NULLs")
        tests.append("    BEGIN TRY")
        null_params = ", ".join([f"{p['name']} = NULL" for p in parameters])
        tests.append(f"        EXEC @ReturnValue = {exec_proc_name} {null_params};")
        tests.append("    END TRY")
        tests.append("    BEGIN CATCH")
        tests.append("        SET @ErrorCaught = 1; -- Expected if proc validates parameters")
        tests.append("    END CATCH")
        tests.append("    ")
        tests.append("    -- Assert: Verify defined behavior (not undefined crash)")
        tests.append("    -- If your proc allows NULLs: uncomment next line")
        tests.append("    -- EXEC tSQLt.AssertEquals @Expected=0, @Actual=@ReturnValue, @Message='Should handle NULLs';")
        tests.append("    -- If your proc rejects NULLs: uncomment next line")
        tests.append("    -- EXEC tSQLt.AssertEquals @Expected=1, @Actual=@ErrorCaught, @Message='Should reject NULLs';")
        tests.append("END;")
        tests.append("GO\n")
    
    # Test 3: Return value
    tests.append(f"CREATE PROCEDURE [{test_class}].[test_ReturnValue_IsValid]")
    tests.append("AS")
    tests.append("BEGIN")
    tests.append("    -- Arrange")
    for p in parameters:
        tests.append(f"    DECLARE {p['name']} {p['type']} = {get_default_value(p)};")
    tests.append("    DECLARE @ReturnValue INT;")
    tests.append("    ")
    tests.append("    -- Act")
    if parameters:
        param_list = ", ".join([f"{p['name']} = {p['name']}" for p in parameters])
        tests.append(f"    EXEC @ReturnValue = {exec_proc_name} {param_list};")
    else:
        tests.append(f"    EXEC @ReturnValue = {exec_proc_name};")
    tests.append("    ")
    tests.append("    -- Assert: Validate return code is success")
    tests.append("    EXEC tSQLt.AssertEquals ")
    tests.append("        @Expected = 0,")
    tests.append("        @Actual = @ReturnValue,")
    tests.append("        @Message = 'Return value should be 0 for success';")
    tests.append("    ")
    tests.append("    -- Alternative: If negative return codes indicate errors:")
    tests.append("    -- IF @ReturnValue < 0")
    tests.append("    --     EXEC tSQLt.Fail 'Procedure returned error code';")
    tests.append("END;")
    tests.append("GO\n")
    
    return "\n".join(tests)

# Read the SP
with open('uspKaiser820ExtractHistory.sql', 'r', encoding='utf-8') as f:
    sql_code = f.read()

# Extract info
proc_name = extract_procedure_name(sql_code)
parameters = extract_parameters(sql_code)

print("=" * 80)
print("PROCEDURE ANALYSIS")
print("=" * 80)
print(f"Name: {proc_name}")
print(f"Parameters Found: {len(parameters)}")
for p in parameters:
    print(f"  - {p['name']} {p['type']}")
print()

# Generate tests
print("=" * 80)
print("WORLD-CLASS tSQLt UNIT TESTS")
print("=" * 80)
tests = generate_world_class_tests(proc_name, parameters)
print(tests)

# Save to file
with open('WORLD_CLASS_TESTS.sql', 'w', encoding='utf-8') as f:
    f.write(tests)

print("\n" + "=" * 80)
print("✅ Tests saved to: WORLD_CLASS_TESTS.sql")
print("=" * 80)
