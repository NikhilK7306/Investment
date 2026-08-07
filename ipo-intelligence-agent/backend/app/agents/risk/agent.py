"""Risk Analysis Agent - Identifies and quantifies investment risks."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, RiskLevel
from app.domain.value_objects.value_objects import RiskFactor
from app.domain.value_objects.value_objects import Percentage
from app.core.exceptions.base import AgentError


class RiskAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that performs comprehensive risk analysis."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.RISK,
            description="Identifies and quantifies financial, market, operational, and regulatory risks",
            version="1.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are a senior risk analyst specializing in pre-IPO risk assessment.

Your task is to identify, quantify, and prioritize risks for a company going public.

RISK FRAMEWORK:

1. FINANCIAL RISKS
   - Revenue concentration (customer, product, geography)
   - Margin sustainability and compression
   - Debt burden and refinancing risk
   - Working capital volatility
   - Cash burn rate vs runway
   - Accounting quality and aggressiveness

2. MARKET RISKS
   - TAM overestimation
   - Competitive disruption
   - Technology obsolescence
   - Customer adoption risk
   - Pricing power erosion
   - Cyclical sensitivity

3. OPERATIONAL RISKS
   - Key person dependency
   - Supply chain concentration
   - Scaling challenges
   - Quality control
   - Cybersecurity
   - Regulatory compliance

4. REGULATORY & LEGAL RISKS
   - Pending litigation
   - Regulatory investigations
   - Compliance gaps
   - IP infringement risk
   - Data privacy (GDPR, CCPA)
   - Industry-specific regulations

5. GOVERNANCE & STRUCTURAL RISKS
   - Dual-class shares
   - Insider control
   - Related party transactions
   - Board independence
   - Audit committee quality
   - Lockup structure

6. POST-IPO SPECIFIC RISKS
   - Lockup expiration overhang
   - Volatility and liquidity
   - Analyst coverage risk
   - Index inclusion uncertainty
   - Short selling pressure

QUANTIFICATION:
For each risk, provide:
- Category and specific factor
- Severity (Very Low to Extreme)
- Probability (0-100%)
- Impact (0-100%)
- Risk score = Probability × Impact × Severity multiplier
- Evidence and reasoning
- Mitigation strategies

OUTPUT:
- Overall risk level (Very Low to Extreme)
- Top 10 risks ranked by score
- Risk heatmap
- Scenario analysis (base/bear/bull)
- Red flags requiring immediate attention"""
    
    @property
    def available_tools(self) -> List[str]:
        return [
            "analyze_financial_risks",
            "analyze_market_risks",
            "analyze_operational_risks",
            "analyze_regulatory_risks",
            "analyze_governance_risks",
            "analyze_post_ipo_risks",
            "calculate_risk_scores",
            "generate_risk_heatmap",
        ]
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute risk analysis."""
        start_time = datetime.utcnow()
        
        try:
            # Extract data
            financials = input_data.get("financials", [])
            company_profile = input_data.get("company_profile", {})
            market_analysis = input_data.get("market_analysis", {})
            competitive_analysis = input_data.get("competitive_analysis", {})
            legal_data = input_data.get("legal_data", {})
            ipo_details = input_data.get("ipo_details", {})
            
            # Parse latest financials
            latest = financials[0] if financials else {}
            
            # Analyze each risk category
            financial_risks = self._analyze_financial_risks(latest, financials, ipo_details)
            market_risks = self._analyze_market_risks(market_analysis, competitive_analysis, company_profile)
            operational_risks = self._analyze_operational_risks(company_profile, financials)
            regulatory_risks = self._analyze_regulatory_risks(legal_data, company_profile)
            governance_risks = self._analyze_governance_risks(company_profile, ipo_details)
            post_ipo_risks = self._analyze_post_ipo_risks(ipo_details, company_profile)
            
            # Combine all risks
            all_risks = (
                financial_risks + market_risks + operational_risks +
                regulatory_risks + governance_risks + post_ipo_risks
            )
            
            # Calculate scores and rank
            ranked_risks = self._rank_risks(all_risks)
            
            # Determine overall risk level
            overall_risk = self._determine_overall_risk(ranked_risks)
            
            # Generate scenarios
            scenarios = self._generate_scenarios(ranked_risks, latest)
            
            # Identify red flags
            red_flags = self._identify_red_flags(ranked_risks)
            
            result_data = {
                "overall_risk_level": overall_risk.value,
                "overall_risk_score": self._calculate_overall_score(ranked_risks),
                "risk_count": len(all_risks),
                "high_priority_risks": len([r for r in ranked_risks if r.severity in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.EXTREME]]),
                "top_risks": [r.to_dict() for r in ranked_risks[:10]],
                "all_risks": [r.to_dict() for r in ranked_risks],
                "risk_by_category": self._group_by_category(ranked_risks),
                "scenarios": scenarios,
                "red_flags": red_flags,
                "mitigation_summary": self._summarize_mitigations(ranked_risks),
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            confidence = self._calculate_confidence(financials, company_profile, legal_data)
            
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                confidence=confidence,
                reasoning=self._generate_reasoning(result_data),
                evidence=self._collect_evidence(ranked_risks),
                duration_ms=duration,
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration,
            )
    
    def _analyze_financial_risks(
        self,
        latest: Dict,
        history: List[Dict],
        ipo_details: Dict,
    ) -> List[RiskFactor]:
        """Analyze financial risks."""
        risks = []
        
        # Revenue concentration
        rev_concentration = latest.get("revenue_concentration", {})
        top_customer_pct = rev_concentration.get("top_customer_pct", 0)
        top_5_customers_pct = rev_concentration.get("top_5_customers_pct", 0)
        
        if top_customer_pct > 0.3:
            risks.append(RiskFactor(
                category="Financial",
                factor="Revenue Concentration - Single Customer",
                severity=RiskLevel.HIGH if top_customer_pct > 0.5 else RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.7),
                impact=Percentage.from_decimal(0.8),
                description=f"Top customer represents {top_customer_pct:.0%} of revenue",
                evidence=[f"Top customer: {top_customer_pct:.0%}", f"Top 5: {top_5_customers_pct:.0%}"],
                mitigation="Diversify customer base; negotiate longer contracts",
            ))
        
        # Margin compression
        gross_margin = latest.get("gross_margin")
        if gross_margin and gross_margin < 0.5:
            risks.append(RiskFactor(
                category="Financial",
                factor="Low Gross Margin",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.6),
                impact=Percentage.from_decimal(0.5),
                description=f"Gross margin of {gross_margin:.1%} limits profitability buffer",
                evidence=[f"Gross margin: {gross_margin:.1%}"],
                mitigation="Focus on higher-margin products; improve pricing power",
            ))
        
        # Margin trend
        if len(history) >= 2:
            prev_margin = history[1].get("gross_margin", 0)
            if gross_margin and gross_margin < prev_margin - 0.05:
                risks.append(RiskFactor(
                    category="Financial",
                    factor="Margin Compression",
                    severity=RiskLevel.HIGH,
                    probability=Percentage.from_decimal(0.8),
                    impact=Percentage.from_decimal(0.7),
                    description=f"Gross margin declined {prev_margin - gross_margin:.1%} YoY",
                    evidence=[f"Previous: {prev_margin:.1%}", f"Current: {gross_margin:.1%}"],
                    mitigation="Identify cost drivers; renegotiate supplier contracts",
                ))
        
        # Debt levels
        total_debt = latest.get("total_debt", 0)
        ebitda = latest.get("ebitda", 1)
        debt_to_ebitda = total_debt / ebitda if ebitda > 0 else 999
        
        if debt_to_ebitda > 5:
            risks.append(RiskFactor(
                category="Financial",
                factor="High Leverage",
                severity=RiskLevel.HIGH if debt_to_ebitda > 7 else RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.7),
                impact=Percentage.from_decimal(0.8),
                description=f"Debt/EBITDA of {debt_to_ebitda:.1f}x exceeds comfort zone",
                evidence=[f"Debt/EBITDA: {debt_to_ebitda:.1f}x", f"Total debt: ${total_debt:,.0f}"],
                mitigation="Use IPO proceeds to pay down debt; refinance at lower rates",
            ))
        
        # Cash burn
        fcf = latest.get("free_cash_flow", 0)
        cash = latest.get("cash_and_equivalents", 0)
        if fcf < 0 and cash > 0:
            runway = cash / abs(fcf) if fcf != 0 else 999
            if runway < 12:
                risks.append(RiskFactor(
                    category="Financial",
                    factor="Cash Runway Risk",
                    severity=RiskLevel.VERY_HIGH if runway < 6 else RiskLevel.HIGH,
                    probability=Percentage.from_decimal(0.9),
                    impact=Percentage.from_decimal(0.9),
                    description=f"Only {runway:.0f} months of runway at current burn",
                    evidence=[f"Cash: ${cash:,.0f}", f"Monthly burn: ${abs(fcf)/12:,.0f}"],
                    mitigation="IPO proceeds critical; reduce discretionary spend",
                ))
        
        # Revenue growth deceleration
        if len(history) >= 3:
            rev_growth = [h.get("revenue_growth_yoy", 0) for h in history[:3]]
            if rev_growth[0] < rev_growth[1] < rev_growth[2]:
                risks.append(RiskFactor(
                    category="Financial",
                    factor="Revenue Growth Deceleration",
                    severity=RiskLevel.MODERATE,
                    probability=Percentage.from_decimal(0.7),
                    impact=Percentage.from_decimal(0.6),
                    description="Revenue growth slowing for 3+ consecutive periods",
                    evidence=[f"Growth trend: {rev_growth[2]:.1%} → {rev_growth[1]:.1%} → {rev_growth[0]:.1%}"],
                    mitigation="New product launches; market expansion; M&A",
                ))
        
        return risks
    
    def _analyze_market_risks(
        self,
        market_analysis: Dict,
        competitive_analysis: Dict,
        company_profile: Dict,
    ) -> List[RiskFactor]:
        """Analyze market risks."""
        risks = []
        
        # TAM realism
        tam = market_analysis.get("tam_analysis", {})
        tam_score = tam.get("score", 50)
        if tam_score < 40:
            risks.append(RiskFactor(
                category="Market",
                factor="Limited Market Opportunity",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.6),
                impact=Percentage.from_decimal(0.7),
                description=f"TAM attractiveness score low: {tam_score}/100",
                evidence=[f"TAM score: {tam_score}", f"TAM: {tam.get('tam_formatted', 'N/A')}"],
                mitigation="Validate TAM assumptions; explore adjacent markets",
            ))
        
        # Competitive intensity
        comp = competitive_analysis.get("competitive_analysis", {})
        intensity = comp.get("intensity", "moderate")
        if intensity in ["high", "very_high"]:
            risks.append(RiskFactor(
                category="Market",
                factor="Intense Competition",
                severity=RiskLevel.HIGH if intensity == "very_high" else RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.8),
                impact=Percentage.from_decimal(0.7),
                description=f"Competitive intensity: {intensity} ({comp.get('total_competitors', 0)} competitors)",
                evidence=[f"Competitors: {comp.get('total_competitors', 0)}", f"Direct: {comp.get('direct_competitors', 0)}"],
                mitigation="Strengthen differentiation; build switching costs; focus on niche",
            ))
        
        # Weak moat
        moat = comp.get("moat_strength", "moderate")
        if moat == "weak":
            risks.append(RiskFactor(
                category="Market",
                factor="Weak Competitive Moat",
                severity=RiskLevel.HIGH,
                probability=Percentage.from_decimal(0.7),
                impact=Percentage.from_decimal(0.8),
                description="Company lacks sustainable competitive advantages",
                evidence=["Moat assessment: weak", f"Advantages: {company_profile.get('competitive_advantages', [])}"],
                mitigation="Invest in IP; build network effects; increase switching costs",
            ))
        
        # Market timing
        trends = market_analysis.get("trends_analysis", {})
        timing = trends.get("timing_assessment", "fair")
        if timing in ["challenging", "fair"]:
            risks.append(RiskFactor(
                category="Market",
                factor="Unfavorable Market Timing",
                severity=RiskLevel.MODERATE if timing == "fair" else RiskLevel.HIGH,
                probability=Percentage.from_decimal(0.6),
                impact=Percentage.from_decimal(0.5),
                description=f"Market entry timing assessed as {timing}",
                evidence=[f"Lifecycle: {trends.get('lifecycle', 'unknown')}", f"CAGR: {trends.get('cagr', 0):.0%}"],
                mitigation="Accelerate go-to-market; consider delaying if possible",
            ))
        
        return risks
    
    def _analyze_operational_risks(
        self,
        company_profile: Dict,
        financials: List[Dict],
    ) -> List[RiskFactor]:
        """Analyze operational risks."""
        risks = []
        
        # Key person risk
        key_people = company_profile.get("key_people", [])
        if len(key_people) <= 2:
            risks.append(RiskFactor(
                category="Operational",
                factor="Key Person Dependency",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.5),
                impact=Percentage.from_decimal(0.7),
                description=f"Only {len(key_people)} key executives identified",
                evidence=[f"Key people: {len(key_people)}", f"Names: {key_people}"],
                mitigation="Succession planning; key person insurance; distribute responsibilities",
            ))
        
        # Employee concentration
        employee_count = company_profile.get("employee_count", 0)
        if employee_count < 50:
            risks.append(RiskFactor(
                category="Operational",
                factor="Small Team / Scaling Risk",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.6),
                impact=Percentage.from_decimal(0.5),
                description=f"Only {employee_count} employees may struggle to scale post-IPO",
                evidence=[f"Employee count: {employee_count}"],
                mitigation="Aggressive hiring plan; outsource non-core; implement systems",
            ))
        
        # Geographic concentration
        hq = company_profile.get("headquarters", "")
        if hq and "china" in hq.lower():
            risks.append(RiskFactor(
                category="Operational",
                factor="Geopolitical / China Risk",
                severity=RiskLevel.HIGH,
                probability=Percentage.from_decimal(0.5),
                impact=Percentage.from_decimal(0.9),
                description="Headquartered in China - regulatory, delisting, audit risks",
                evidence=[f"HQ: {hq}"],
                mitigation="Dual listing consideration; VIE structure review; audit compliance",
            ))
        
        return risks
    
    def _analyze_regulatory_risks(
        self,
        legal_data: Dict,
        company_profile: Dict,
    ) -> List[RiskFactor]:
        """Analyze regulatory and legal risks."""
        risks = []
        
        # Pending litigation
        litigation = legal_data.get("pending_litigation", [])
        if litigation:
            severity = RiskLevel.HIGH if len(litigation) > 3 else RiskLevel.MODERATE
            risks.append(RiskFactor(
                category="Regulatory",
                factor="Pending Litigation",
                severity=severity,
                probability=Percentage.from_decimal(0.4),
                impact=Percentage.from_decimal(0.6),
                description=f"{len(litigation)} pending legal matters",
                evidence=[f"Cases: {len(litigation)}", f"Details: {[l.get('description', '') for l in litigation[:3]]}"],
                mitigation="Legal reserves; settlement planning; insurance review",
            ))
        
        # Regulatory investigations
        investigations = legal_data.get("investigations", [])
        if investigations:
            risks.append(RiskFactor(
                category="Regulatory",
                factor="Regulatory Investigation",
                severity=RiskLevel.VERY_HIGH,
                probability=Percentage.from_decimal(0.3),
                impact=Percentage.from_decimal(0.9),
                description=f"Under investigation by {len(investigations)} regulatory bodies",
                evidence=[f"Investigations: {len(investigations)}", f"Agencies: {[i.get('agency', '') for i in investigations]}"],
                mitigation="Cooperate fully; enhance compliance; legal defense fund",
            ))
        
        # Industry-specific regulation
        industry = company_profile.get("industry", "").lower()
        regulated_industries = ["biotech", "pharmaceuticals", "fintech", "healthcare", "energy", "banking"]
        if any(reg in industry for reg in regulated_industries):
            risks.append(RiskFactor(
                category="Regulatory",
                factor=f"Industry Regulation - {industry.title()}",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.6),
                impact=Percentage.from_decimal(0.5),
                description=f"Operating in heavily regulated {industry} sector",
                evidence=[f"Industry: {industry}"],
                mitigation="Dedicated compliance team; regulatory strategy; lobbying",
            ))
        
        return risks
    
    def _analyze_governance_risks(
        self,
        company_profile: Dict,
        ipo_details: Dict,
    ) -> List[RiskFactor]:
        """Analyze governance and structural risks."""
        risks = []
        
        # Dual class shares
        share_structure = ipo_details.get("share_structure", {})
        if share_structure.get("dual_class", False):
            risks.append(RiskFactor(
                category="Governance",
                factor="Dual-Class Share Structure",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.8),
                impact=Percentage.from_decimal(0.4),
                description="Dual-class shares concentrate voting control with insiders",
                evidence=["Dual-class structure confirmed", f"Insider voting control: {share_structure.get('insider_voting_pct', 'N/A')}%"],
                mitigation="Sunset provision; independent board oversight; shareholder engagement",
            ))
        
        # Insider control
        insider_control = share_structure.get("insider_voting_pct", 0)
        if insider_control > 50:
            risks.append(RiskFactor(
                category="Governance",
                factor="Insider Control",
                severity=RiskLevel.MODERATE if insider_control < 70 else RiskLevel.HIGH,
                probability=Percentage.from_decimal(0.9),
                impact=Percentage.from_decimal(0.4),
                description=f"Insiders control {insider_control:.0f}% of voting power",
                evidence=[f"Insider voting: {insider_control:.0f}%"],
                mitigation="Independent directors; committee independence; shareholder proposals",
            ))
        
        # Board independence
        board = company_profile.get("board_members", [])
        independent = [b for b in board if b.get("independent", False)]
        if len(board) > 0 and len(independent) / len(board) < 0.5:
            risks.append(RiskFactor(
                category="Governance",
                factor="Insufficient Board Independence",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.7),
                impact=Percentage.from_decimal(0.5),
                description=f"Only {len(independent)}/{len(board)} directors are independent",
                evidence=[f"Board size: {len(board)}", f"Independent: {len(independent)}"],
                mitigation="Add independent directors; separate chair/CEO roles",
            ))
        
        # Lockup structure
        lockup_days = ipo_details.get("lockup_period_days", 180)
        if lockup_days < 180:
            risks.append(RiskFactor(
                category="Governance",
                factor="Short Lockup Period",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.6),
                impact=Percentage.from_decimal(0.4),
                description=f"Lockup only {lockup_days} days - early insider selling pressure",
                evidence=[f"Lockup: {lockup_days} days"],
                mitigation="Staggered lockup releases; insider selling plans (10b5-1)",
            ))
        
        return risks
    
    def _analyze_post_ipo_risks(
        self,
        ipo_details: Dict,
        company_profile: Dict,
    ) -> List[RiskFactor]:
        """Analyze post-IPO specific risks."""
        risks = []
        
        # Lockup expiration
        lockup_days = ipo_details.get("lockup_period_days", 180)
        insider_shares = ipo_details.get("insider_shares_pct", 0)
        
        if insider_shares > 0.3:
            risks.append(RiskFactor(
                category="Post-IPO",
                factor="Lockup Expiration Overhang",
                severity=RiskLevel.HIGH if insider_shares > 0.5 else RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.9),
                impact=Percentage.from_decimal(0.6),
                description=f"Insiders hold {insider_shares:.0%} - significant selling pressure at lockup expiry",
                evidence=[f"Insider ownership: {insider_shares:.0%}", f"Lockup expiry: {lockup_days} days"],
                mitigation="Staggered releases; 10b5-1 plans; communicate holding intentions",
            ))
        
        # Small float
        float_pct = ipo_details.get("float_pct", 0)
        if float_pct < 0.15:
            risks.append(RiskFactor(
                category="Post-IPO",
                factor="Low Public Float",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.7),
                impact=Percentage.from_decimal(0.5),
                description=f"Only {float_pct:.0%} float - liquidity and volatility concerns",
                evidence=[f"Public float: {float_pct:.0%}"],
                mitigation="Follow-on offerings; market maker engagement; buyback program",
            ))
        
        # No analyst coverage expected
        if company_profile.get("employee_count", 0) < 200:
            risks.append(RiskFactor(
                category="Post-IPO",
                factor="Limited Analyst Coverage",
                severity=RiskLevel.MODERATE,
                probability=Percentage.from_decimal(0.8),
                impact=Percentage.from_decimal(0.4),
                description="Small size may limit initial analyst coverage",
                evidence=[f"Employees: {company_profile.get('employee_count', 0)}"],
                mitigation="IR program; investor conferences; targeted outreach",
            ))
        
        return risks
    
    def _rank_risks(self, risks: List[RiskFactor]) -> List[RiskFactor]:
        """Rank risks by risk score."""
        return sorted(risks, key=lambda r: r.risk_score, reverse=True)
    
    def _determine_overall_risk(self, risks: List[RiskFactor]) -> RiskLevel:
        """Determine overall risk level."""
        if not risks:
            return RiskLevel.LOW
        
        # Weight by severity
        severity_weights = {
            RiskLevel.EXTREME: 100,
            RiskLevel.VERY_HIGH: 80,
            RiskLevel.HIGH: 60,
            RiskLevel.MODERATE: 40,
            RiskLevel.LOW: 20,
            RiskLevel.VERY_LOW: 10,
        }
        
        total_weight = sum(severity_weights.get(r.severity, 40) for r in risks[:10])
        avg_weight = total_weight / min(10, len(risks))
        
        if avg_weight >= 80:
            return RiskLevel.EXTREME
        elif avg_weight >= 60:
            return RiskLevel.VERY_HIGH
        elif avg_weight >= 45:
            return RiskLevel.HIGH
        elif avg_weight >= 30:
            return RiskLevel.MODERATE
        elif avg_weight >= 15:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _calculate_overall_score(self, risks: List[RiskFactor]) -> float:
        """Calculate overall risk score (0-100)."""
        if not risks:
            return 10.0
        
        # Average of top 10 risk scores
        top_risks = risks[:10]
        return sum(r.risk_score for r in top_risks) / len(top_risks)
    
    def _group_by_category(self, risks: List[RiskFactor]) -> Dict[str, List[Dict]]:
        """Group risks by category."""
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in risks:
            grouped[r.category].append(r.to_dict())
        return dict(grouped)
    
    def _generate_scenarios(
        self,
        risks: List[RiskFactor],
        financials: Dict,
    ) -> Dict[str, Dict]:
        """Generate base/bear/bull scenarios."""
        base_revenue = financials.get("revenue", 1)
        base_fcf = financials.get("free_cash_flow", 0)
        
        # Calculate risk-adjusted impacts
        high_impact_risks = [r for r in risks if r.impact.to_decimal() > 0.7]
        total_prob_impact = sum(r.probability.to_decimal() * r.impact.to_decimal() for r in high_impact_risks)
        
        bear_impact = min(0.5, total_prob_impact)
        bull_impact = -total_prob_impact * 0.3  # Some risks may not materialize
        
        return {
            "base": {
                "revenue": base_revenue,
                "fcf": base_fcf,
                "probability": 0.5,
            },
            "bear": {
                "revenue": base_revenue * (1 - bear_impact),
                "fcf": base_fcf * (1 - bear_impact * 1.5),
                "probability": 0.25,
                "key_risks": [r.factor for r in high_impact_risks[:5]],
            },
            "bull": {
                "revenue": base_revenue * (1 + abs(bull_impact)),
                "fcf": base_fcf * (1 + abs(bull_impact)),
                "probability": 0.25,
                "assumptions": "Risks mitigated; execution exceeds expectations",
            },
        }
    
    def _identify_red_flags(self, risks: List[RiskFactor]) -> List[str]:
        """Identify critical red flags."""
        red_flags = []
        
        for risk in risks[:10]:
            if risk.severity in [RiskLevel.EXTREME, RiskLevel.VERY_HIGH]:
                if risk.probability.to_decimal() > 0.7 and risk.impact.to_decimal() > 0.7:
                    red_flags.append(
                        f"🚨 {risk.category}: {risk.factor} "
                        f"(Prob: {risk.probability.to_percent():.0f}%, Impact: {risk.impact.to_percent():.0f}%)"
                    )
        
        # Specific patterns
        financial_risks = [r for r in risks if r.category == "Financial"]
        high_financial = [r for r in financial_risks if r.severity in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.EXTREME]]
        if len(high_financial) >= 3:
            red_flags.append("🚨 Multiple high-severity financial risks detected")
        
        regulatory_risks = [r for r in risks if r.category == "Regulatory"]
        if any(r.severity == RiskLevel.VERY_HIGH for r in regulatory_risks):
            red_flags.append("🚨 Critical regulatory risk - potential existential threat")
        
        return red_flags
    
    def _summarize_mitigations(self, risks: List[RiskFactor]) -> Dict[str, List[str]]:
        """Summarize key mitigations by category."""
        from collections import defaultdict
        mitigations = defaultdict(list)
        
        for risk in risks[:15]:  # Top 15
            if risk.mitigation:
                mitigations[risk.category].append(risk.mitigation)
        
        return {k: list(set(v)) for k, v in mitigations.items()}
    
    def _calculate_confidence(
        self,
        financials: List[Dict],
        company_profile: Dict,
        legal_data: Dict,
    ) -> float:
        """Calculate confidence in risk assessment."""
        confidence = 0.5
        
        if len(financials) >= 3:
            confidence += 0.15
        elif len(financials) > 0:
            confidence += 0.1
        
        if company_profile.get("key_people"):
            confidence += 0.05
        
        if legal_data.get("pending_litigation") is not None:
            confidence += 0.1
        
        if company_profile.get("board_members"):
            confidence += 0.05
        
        if company_profile.get("competitive_advantages"):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _generate_reasoning(self, result: Dict) -> str:
        """Generate reasoning summary."""
        parts = [
            f"Overall Risk Level: {result['overall_risk_level'].upper()}",
            f"Risk Score: {result['overall_risk_score']:.1f}/100",
            f"Total Risks Identified: {result['risk_count']}",
            f"High Priority: {result['high_priority_risks']}",
            "",
            "Top 5 Risks:",
        ]
        
        for i, risk in enumerate(result["top_risks"][:5], 1):
            parts.append(
                f"  {i}. [{risk['severity']}] {risk['category']}: {risk['factor']} "
                f"(Score: {risk['risk_score']:.1f})"
            )
        
        if result["red_flags"]:
            parts.append("\n🚨 RED FLAGS:")
            for flag in result["red_flags"]:
                parts.append(f"  {flag}")
        
        return "\n".join(parts)
    
    def _collect_evidence(self, risks: List[RiskFactor]) -> List[str]:
        """Collect evidence from top risks."""
        evidence = []
        for risk in risks[:10]:
            evidence.extend(risk.evidence[:2])
        return evidence[:20]