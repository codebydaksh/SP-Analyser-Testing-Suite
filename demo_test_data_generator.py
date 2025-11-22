"""
Demo script showing TestDataGenerator capabilities
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.testing.test_data_generator import TestDataGenerator


def main():
    gen = TestDataGenerator()
    
    print("="*70)
    print("TEST DATA GENERATOR - Comprehensive Test Data for QA")
    print("="*70)
    
    # Example 1: Email parameter
    print("\n Example 1: Email Parameter (VARCHAR(100))")
    print("-" * 70)
    email_param = {'name': '@Email', 'type': 'VARCHAR(100)'}
    email_data = gen.generate_test_values(email_param)
    
    print(f"Realistic Value: {gen.get_realistic_value(email_param)}")
    print(f"\nValid Values: {email_data['valid'][:3]}")
    print(f"Boundary Values: {email_data['boundary'][:3]}")
    print(f"Edge Cases (SQL Injection): {email_data['edge_cases'][:2]}")
    print(f"Invalid Values: {email_data['invalid'][:1]}")
    
    # Example 2: Integer ID
    print("\n\n Example 2: User ID (INT)")
    print("-" * 70)
    id_param = {'name': '@UserId', 'type': 'INT'}
    id_data = gen.generate_test_values(id_param)
    
    print(f"Realistic Value: {gen.get_realistic_value(id_param)}")
    print(f"\nValid Values: {id_data['valid']}")
    print(f"Boundary Values (MIN/MAX): {id_data['boundary'][:5]}")
    print(f"Edge Cases: {id_data['edge_cases']}")
    print(f"Invalid Values (Overflow): {id_data['invalid'][:2]}")
    
    # Example 3: Date
    print("\n\n Example 3: Order Date (DATETIME)")
    print("-" * 70)
    date_param = {'name': '@OrderDate', 'type': 'DATETIME'}
    date_data = gen.generate_test_values(date_param)
    
    print(f"Realistic Value: {gen.get_realistic_value(date_param)}")
    print(f"\nValid Values: {date_data['valid']}")
    print(f"Boundary Values (SQL Server MIN/MAX): {date_data['boundary'][:3]}")
    print(f"Invalid Values (Bad Dates): {date_data['invalid']}")
    
    # Example 4: Decimal
    print("\n\n Example 4: Price (DECIMAL(18,2))")
    print("-" * 70)
    price_param = {'name': '@Price', 'type': 'DECIMAL(18,2)'}
    price_data = gen.generate_test_values(price_param)
    
    print(f"Realistic Value: {gen.get_realistic_value(price_param)}")
    print(f"\nValid Values: {price_data['valid']}")
    print(f"Boundary Values: {price_data['boundary']}")
    
    print("\n" + "="*70)
    print(" Ready for QA Testing!")
    print("="*70)
    print("\nBenefits:")
    print("  - Boundary value analysis (MIN/MAX)")
    print("  - SQL injection test cases")
    print("  - NULL and edge case handling")
    print("  - Realistic test data")
    print("  - Positive AND negative testing")


if __name__ == '__main__':
    main()
