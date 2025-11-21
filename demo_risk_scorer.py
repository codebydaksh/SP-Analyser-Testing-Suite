"""
Demo: Risk Scoring & Defect Prediction

Shows how RiskScorer helps QA teams prioritize testing
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.risk_scorer import RiskScorer


def main():
    scorer = RiskScorer()
    
    print("="*80)
    print("RISK SCORER - Defect Prediction for QA Teams")
    print("="*80)
    
    # Example 1: LOW RISK procedure
    low_risk_sp = {
        'procedure_name': 'dbo.GetUserById',
        'lines_of_code': 50,
        'parameters': [{'name': '@UserId', 'type': 'INT'}],
        'tables': ['dbo.Users'],
        'security': {'score': 95, 'analysis': {'sql_injection_risks': [], 'permission_issues': [], 'security_warnings': []}},
        'quality': {'score':90, 'grade': 'A'},
        'performance': {'score': 95, 'grade': 'A', 'issues': []},
        'has_try_catch': True
    }
    
    # Example 2: HIGH RISK procedure
    high_risk_sp = {
        'procedure_name': 'dbo.ProcessPaymentWithDynamicSQL',
        'lines_of_code': 650,
        'parameters': [{'name': f'@Param{i}', 'type': 'VARCHAR(100)'} for i in range(15)],
        'tables': ['dbo.Payments', 'dbo.Users', 'dbo.Orders', 'dbo.AuditLog', 'dbo.Transactions', 
                   'dbo.PaymentMethods', 'dbo.Invoices', 'dbo.Customers', 'dbo.Accounts',
                   'dbo.AccountHistory', 'dbo.PaymentHistory', 'dbo.RefundLog', 'dbo.ErrorLog',
                   'dbo.NotificationQueue', 'dbo.EmailQueue', 'dbo.SMSQueue', 'dbo.ProcessLog'],
        'security': {
            'score': 45,
            'analysis': {
                'sql_injection_risks': [
                    {'severity': 'CRITICAL', 'type': 'Dynamic SQL', 'message': 'Unparameterized dynamic SQL with user input'},
                    {'severity': 'HIGH', 'type': 'String Concatenation', 'message': 'String concatenation in WHERE clause'}
                ],
                'permission_issues': [
                    {'severity': 'HIGH', 'type': 'Elevated Permissions', 'message': 'Uses xp_cmdshell'}
                ],
                'security_warnings': []
            }
        },
        'quality': {'score': 55, 'grade': 'F'},
        'performance': {
            'score': 40,
            'grade': 'F',
            'issues': [
                {'severity': 'HIGH', 'issue': 'Cursor usage detected'},
                {'severity': 'HIGH', 'issue': 'Multiple RBAR operations'},
                {'severity': 'MEDIUM', 'issue': 'Missing indexes on JOIN columns'}
            ]
        },
        'has_try_catch': False
    }
    
    # Assess LOW RISK
    print("\n\n📊 Example 1: Simple Procedure")
    print("-" * 80)
    print(f"Procedure: {low_risk_sp['procedure_name']}")
    print(f"LOC: {low_risk_sp['lines_of_code']}, Parameters: {len(low_risk_sp['parameters'])}, Tables: {len(low_risk_sp['tables'])}")
    
    low_assessment = scorer.calculate_risk_score(low_risk_sp)
    print(f"\n{scorer.generate_risk_summary(low_assessment)}")
    
    # Assess HIGH RISK
    print("\n\n📊 Example 2: Complex High-Risk Procedure")
    print("-" * 80)
    print(f"Procedure: {high_risk_sp['procedure_name']}")
    print(f"LOC: {high_risk_sp['lines_of_code']}, Parameters: {len(high_risk_sp['parameters'])}, Tables: {len(high_risk_sp['tables'])}")
    
    high_assessment = scorer.calculate_risk_score(high_risk_sp)
    print(f"\n{scorer.generate_risk_summary(high_assessment)}")
    
    print("\n\n" + "="*80)
    print("QA Testing Priority Queue")
    print("="*80)
    
    procedures = [
        (low_risk_sp, low_assessment),
        (high_risk_sp, high_assessment)
    ]
    
    # Sort by risk score (highest first)
    procedures.sort(key=lambda x: x[1]['risk_score'], reverse=True)
    
    print("\nPriority Order for Testing:")
    for i, (sp, assessment) in enumerate(procedures, 1):
        print(f"{i}. [{assessment['risk_level']}] {sp['procedure_name']} (Risk Score: {assessment['risk_score']})")
    
    print("\n" + "="*80)
    print("✅ Risk-Based Testing Strategy Ready!")
    print("="*80)
    print("\nBenefits for QA:")
    print("  ✓ Prioritize testing on high-risk procedures")
    print("  ✓ Allocate resources efficiently")
    print("  ✓ Identify defect-prone code early")
    print("  ✓ Data-driven testing decisions")


if __name__ == '__main__':
    main()
