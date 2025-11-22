"""
Risk Scorer - Defect Prediction for QA Teams

Aggregate all findings and calculate risk scores to help QA
prioritize testing efforts on high-risk stored procedures.
"""
from typing import Dict, List, Any


class RiskScorer:
    """Calculate risk scores and defect prediction for stored procedures."""
    
    # Severity weights
    SEVERITY_WEIGHTS = {
        'CRITICAL': 10,
        'HIGH': 5,
        'MEDIUM': 2,
        'LOW': 1
    }
    
    def calculate_risk_score(self, sp_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a stored procedure.
        
        Args:
            sp_analysis: Complete analysis result
            
        Returns:
            Risk assessment with score, level, and recommendations
        """
        risk_points = 0
        risk_factors = []
        
        # Factor 1: Security Issues
        security_risk, security_factors = self._assess_security_risk(sp_analysis)
        risk_points += security_risk
        risk_factors.extend(security_factors)
        
        # Factor 2: Quality Issues
        quality_risk, quality_factors = self._assess_quality_risk(sp_analysis)
        risk_points += quality_risk
        risk_factors.extend(quality_factors)
        
        # Factor 3: Performance Issues
        perf_risk, perf_factors = self._assess_performance_risk(sp_analysis)
        risk_points += perf_risk
        risk_factors.extend(perf_factors)
        
        # Factor 4: Complexity
        complexity_risk, complexity_factors = self._assess_complexity_risk(sp_analysis)
        risk_points += complexity_risk
        risk_factors.extend(complexity_factors)
        
        # Determine risk level
        if risk_points >= 30:
            risk_level = 'CRITICAL'
            recommendation = ' HIGH PRIORITY: Intensive testing required. Consider code review before deployment.'
        elif risk_points >= 15:
            risk_level = 'HIGH'
            recommendation = '  ELEVATED RISK: Thorough testing recommended. Focus on edge cases.'
        elif risk_points >= 8:
            risk_level = 'MEDIUM'
            recommendation = ' MODERATE RISK: Standard testing procedures apply.'
        else:
            risk_level = 'LOW'
            recommendation = ' LOW RISK: Basic smoke testing sufficient.'
        
        return {
            'risk_score': risk_points,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'risk_factors': risk_factors,
            'breakdown': {
                'security': security_risk,
                'quality': quality_risk,
                'performance': perf_risk,
                'complexity': complexity_risk
            }
        }
    
    def _assess_security_risk(self, sp_analysis: Dict[str, Any]) -> tuple:
        """Assess security-related risk."""
        risk_points = 0
        factors = []
        
        security = sp_analysis.get('security', {})
        score = security.get('score', 100)
        
        # Low security score = high risk
        if score < 50:
            risk_points += 15
            factors.append({'category': 'Security', 'severity': 'CRITICAL', 'issue': f'Security score {score} is critically low'})
        elif score < 70:
            risk_points += 8
            factors.append({'category': 'Security', 'severity': 'HIGH', 'issue': f'Security score {score} below threshold'})
        
        # Check specific risks
        analysis = security.get('analysis', {})
        sql_injection = analysis.get('sql_injection_risks', [])
        
        for risk in sql_injection:
            severity = risk.get('severity', 'LOW')
            risk_points += self.SEVERITY_WEIGHTS.get(severity, 1)
            factors.append({
                'category': 'Security',
                'severity': severity,
                'issue': risk.get('message', 'SQL Injection risk')
            })
        
        return risk_points, factors
    
    def _assess_quality_risk(self, sp_analysis: Dict[str, Any]) -> tuple:
        """Assess code quality-related risk."""
        risk_points = 0
        factors = []
        
        quality = sp_analysis.get('quality', {})
        score = quality.get('score', 100)
        
        if score < 60:
            risk_points += 10
            factors.append({'category': 'Quality', 'severity': 'HIGH', 'issue': f'Quality score {score} is poor'})
        elif score < 80:
            risk_points += 4
            factors.append({'category': 'Quality', 'severity': 'MEDIUM', 'issue': f'Quality score {score} needs improvement'})
        
        # Check error handling
        if not sp_analysis.get('has_try_catch', False):
            risk_points += 5
            factors.append({'category': 'Quality', 'severity': 'HIGH', 'issue': 'No error handling (TRY-CATCH) found'})
        
        return risk_points, factors
    
    def _assess_performance_risk(self, sp_analysis: Dict[str, Any]) -> tuple:
        """Assess performance-related risk."""
        risk_points = 0
        factors = []
        
        performance = sp_analysis.get('performance', {})
        score = performance.get('score', 100)
        
        if score < 60:
            risk_points += 8
            factors.append({'category': 'Performance', 'severity': 'HIGH', 'issue': f'Performance score {score} indicates serious issues'})
        elif score < 80:
            risk_points += 3
            factors.append({'category': 'Performance', 'severity': 'MEDIUM', 'issue': f'Performance score {score} could be optimized'})
        
        # Check specific issues
        issues = performance.get('issues', [])
        for issue in issues:
            severity = issue.get('severity', 'LOW')
            risk_points += self.SEVERITY_WEIGHTS.get(severity, 1)
            factors.append({
                'category': 'Performance',
                'severity': severity,
                'issue': issue.get('issue', 'Performance concern')
            })
        
        return risk_points, factors
    
    def _assess_complexity_risk(self, sp_analysis: Dict[str, Any]) -> tuple:
        """Assess complexity-related risk."""
        risk_points = 0
        factors = []
        
        loc = sp_analysis.get('lines_of_code', 0)
        param_count = len(sp_analysis.get('parameters', []))
        table_count = len(sp_analysis.get('tables', []))
        
        # Large procedures are riskier
        if loc > 500:
            risk_points += 8
            factors.append({'category': 'Complexity', 'severity': 'HIGH', 'issue': f'{loc} lines of code - very large procedure'})
        elif loc > 200:
            risk_points += 3
            factors.append({'category': 'Complexity', 'severity': 'MEDIUM', 'issue': f'{loc} lines of code - large procedure'})
        
        # Many parameters = complex interface
        if param_count > 10:
            risk_points += 5
            factors.append({'category': 'Complexity', 'severity': 'MEDIUM', 'issue': f'{param_count} parameters - complex interface'})
        
        # Many tables = complex dependencies
        if table_count > 15:
            risk_points += 4
            factors.append({'category': 'Complexity', 'severity': 'MEDIUM', 'issue': f'{table_count} tables - many dependencies'})
        
        return risk_points, factors
    
    def generate_risk_summary(self, risk_assessment: Dict[str, Any]) -> str:
        """Generate human-readable risk summary."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"RISK ASSESSMENT: {risk_assessment['risk_level']}")
        lines.append("=" * 70)
        lines.append(f"Risk Score: {risk_assessment['risk_score']}")
        lines.append(f"Recommendation: {risk_assessment['recommendation']}")
        lines.append("")
        lines.append("Risk Breakdown:")
        breakdown = risk_assessment['breakdown']
        lines.append(f"  - Security:    {breakdown['security']} points")
        lines.append(f"  - Quality:     {breakdown['quality']} points")
        lines.append(f"  - Performance: {breakdown['performance']} points")
        lines.append(f"  - Complexity:  {breakdown['complexity']} points")
        lines.append("")
        lines.append(f"Key Risk Factors ({len(risk_assessment['risk_factors'])} total):")
        for factor in risk_assessment['risk_factors'][:5]:  # Top 5
            lines.append(f"  [{factor['severity']}] {factor['issue']}")
        lines.append("=" * 70)
        
        return "\n".join(lines)
