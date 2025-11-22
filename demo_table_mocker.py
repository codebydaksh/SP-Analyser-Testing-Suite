"""
Demo: Table Mocking with tSQLt.FakeTable

Shows how TableMocker automatically generates:
- FakeTable calls for dependencies
- Fixture data
- Setup/TearDown methods
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.testing.table_mocker import TableMocker


def main():
    mocker = TableMocker()
    
    print("="*80)
    print("TABLE MOCKER - Automatic tSQLt.FakeTable Generation")
    print("="*80)
    
    # Example: SP that uses multiple tables
    sp_analysis = {
        'name': 'dbo.ProcessOrder',
        'tables': ['dbo.Users', 'dbo.Orders', 'dbo.OrderItems', '#TempResults', 'dbo.AuditLog']
    }
    
    print("\n Sample Stored Procedure Analysis:")
    print(f"   Name: {sp_analysis['name']}")
    print(f"   Tables Referenced: {', '.join(sp_analysis['tables'])}")
    
    # Extract dependencies (filters out temp tables)
    dependencies = mocker.extract_table_dependencies(sp_analysis)
    print(f"\n Real Tables to Mock: {dependencies}")
    print(f"   (Temp tables like #TempResults are excluded)")
    
    # Generate FakeTable calls
    print("\n\n Generated tSQLt.FakeTable Calls:")
    print("-" * 80)
    fake_calls = mocker.generate_fake_table_calls(dependencies)
    for call in fake_calls:
        print(call)
    
    # Generate fixture data
    print("\n\n Generated Fixture Data (Basic Scenario):")
    print("-" * 80)
    fixture_data = mocker.create_fixture_data(dependencies, 'basic')
    for stmt in fixture_data:
        print(stmt)
    
    # Generate complete setup/teardown
    print("\n\n Complete Setup/TearDown Methods:")
    print("-" * 80)
    setup_teardown = mocker.generate_setup_teardown('TestProcessOrder', dependencies, 'basic')
    print(setup_teardown)
    
    # Generate complete test with mocks
    print("\n\n Complete Test with Automatic Mocking:")
    print("=" * 80)
    parameters = [
        {'name': '@UserId', 'type': 'INT'},
        {'name': '@OrderId', 'type': 'INT'}
    ]
    complete_test = mocker.generate_complete_test_with_mocks(
        'dbo.ProcessOrder',
        parameters,
        dependencies
    )
    print(complete_test)
    
    print("\n" + "="*80)
    print(" Ready for Production Testing!")
    print("="*80)
    print("\nBenefits:")
    print("  - Automatic table dependency detection")
    print("  - No manual FakeTable calls needed")
    print("  - Fixture data pre-populated")
    print("  - Clean setup/teardown structure")
    print("  - Tests run in isolation")


if __name__ == '__main__':
    main()
