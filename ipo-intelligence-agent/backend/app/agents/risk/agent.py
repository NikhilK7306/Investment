"""Risk Analysis Agent - Identifies and quantifies investment risks using LLM."""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, RiskLevel
from app.domain.value_objects.value_objects import RiskFactor, Percentage
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class RiskFactorOutput(BaseModel):
    """Individual risk factor output."""
    category: str
    factor: str
    severity: str = Field(pattern="^(VERY_LOW|LOW|MODERATE|HIGH|VERY_HIGH|EXTREME)$")
    probability: float = Field(ge=0, le=1)
    impact: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0)
    description: str
    evidence: List[str] = []
    mitigation: str = ""


class RiskAnalysisOutput(BaseModel):
    """Structured output for risk analysis."""
    overall_risk_level: str = Field(pattern="^(VERY_LOW|LOW|MODERATE|HIGH|VERY_HIGH|EXTREME)$")
    overall_risk_score: float = Field(ge=0, le=100)
    risk_count: int
    high_priority_risks: int
    top_risks: List[RiskFactorOutput]
    all_risks: List[RiskFactorOutput]
    risk_by_category: Dict[str, List[RiskFactorOutput]]
    scenarios: Dict[str, Dict[str, Any]]
    red_flags: List[str]
    mitigation_summary: Dict[str, List[str]]
    reasoning: str
    confidence: float = Field(ge=0, le=1)


class RiskAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that performs comprehensive risk analysis using LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.RISK,
            description="Identifies and quantifies financial, market, operational, and regulatory risks using LLM",
            version="2.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
        self._llm_provider = None

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
- Red flags requiring immediate attention

CRITICAL: Use ONLY the supplied verified data. If information is unavailable, return null/Not Available. Do NOT infer or fabricate factual values. Distinguish clearly between verified facts and your analytical interpretation."""

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

    def _get_llm_provider(self):
        if self._llm_provider is None:
            self._llm_provider = LLMProviderFactory.create_from_env()
        return self._llm_provider

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        start_time = datetime.utcnow()

        try:
            financials = input_data.get("financials", [])
            company_profile = input_data.get("company_profile", {})
            market_analysis = input_data.get("market_analysis", {})
            competitive_analysis = input_data.get("competitive_analysis", {})
            legal_data = input_data.get("legal_data", {})
            ipo_details = input_data.get("ipo_details", {})

            # Check for critical missing data
            if not financials:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error="No financial data provided for risk analysis",
                    error_type="INSUFFICIENT_DATA",
                    data={"data_quality": "none", "reason": "Missing financial statements"},
                )

            if not company_profile or not company_profile.get("common_name"):
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error="No company profile data provided",
                    error_type="INSUFFICIENT_DATA",
                    data={"data_quality": "insufficient", "reason": "Missing company profile"},
                )

            provider = self._get_llm_provider()
            await provider.initialize()

            risk_summary = self._prepare_risk_summary(
                financials, company_profile, market_analysis, 
                competitive_analysis, legal_data, ipo_details
            )

            prompt = self._create_analysis_prompt(risk_summary)

            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=4000,
                response_model=RiskAnalysisOutput,
            )

            if isinstance(response.content, str):
                try:
                    analysis_data = json.loads(response.content)
                except json.JSONDecodeError:
                    analysis_data = self._extract_json(response.content)
            else:
                analysis_data = response.content

            analysis = RiskAnalysisOutput(**analysis_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=analysis.model_dump(),
                confidence=analysis.confidence,
                reasoning=analysis.reasoning,
                evidence=self._collect_evidence(risk_summary),
                duration_ms=duration,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
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

    def _prepare_risk_summary(
        self,
        financials: List,
        company_profile: Dict,
        market_analysis: Dict,
        competitive_analysis: Dict,
        legal_data: Dict,
        ipo_details: Dict,
    ) -> Dict[str, Any]:
        """Prepare verified data for risk analysis."""
        
        def safe_get(d: Dict, key: str, default="Not Available"):
            return d.get(key, default)
        
        latest = financials[0] if financials else {}
        
        summary = {
            "financials": {
                "revenue": latest.get("revenue"),
                "revenue_growth_yoy": latest.get("revenue_growth_yoy"),
                "gross_margin": latest.get("gross_margin"),
                "operating_margin": latest.get("operating_margin"),
                "net_income": latest.get("net_income"),
                "ebitda": latest.get("ebitda"),
                "free_cash_flow": latest.get("free_cash_flow"),
                "cash_and_equivalents": latest.get("cash_and_equivalents"),
                "total_debt": latest.get("total_debt"),
                "total_equity": latest.get("total_equity"),
                "debt_to_equity": latest.get("debt_to_equity"),
                "current_ratio": latest.get("current_ratio"),
                "quick_ratio": latest.get("quick_ratio"),
                "interest_coverage": latest.get("interest_coverage"),
                "historical_periods": len(financials),
                "revenue_history": [
                    {"period": f.get("period"), "revenue": f.get("revenue"), 
                     "growth": f.get("revenue_growth_yoy")}
                    for f in financials[:4]
                ],
            },
            "company_profile": {
                "key_people": company_profile.get("key_people", []),
                "employee_count": company_profile.get("employee_count"),
                "headquarters": company_profile.get("headquarters"),
                "board_members": company_profile.get("board_members", []),
                "competitive_advantages": company_profile.get("competitive_advantages", []),
            },
            "market_analysis": {
                "tam_score": market_analysis.get("tam_analysis", {}).get("score"),
                "competitive_intensity": market_analysis.get("competitive_analysis", {}).get("intensity"),
                "moat_strength": market_analysis.get("competitive_analysis", {}).get("moat_strength"),
                "total_competitors": market_analysis.get("competitive_analysis", {}).get("total_competitors"),
                "direct_competitors": market_analysis.get("competitive_analysis", {}).get("direct_competitors"),
                "timing_assessment": market_analysis.get("trends_analysis", {}).get("timing_assessment"),
                "lifecycle": market_analysis.get("trends_analysis", {}).get("lifecycle"),
                "cagr": market_analysis.get("trends_analysis", {}).get("cagr"),
                "tailwinds": market_analysis.get("trends_analysis", {}).get("tailwinds", []),
                "headwinds": market_analysis.get("trends_analysis", {}).get("headwinds", []),
            },
            "competitive_analysis": competitive_analysis,
            "legal_data": {
                "pending_litigation": legal_data.get("pending_litigation", []),
                "investigations": legal_data.get("investigations", []),
            },
            "ipo_details": {
                "share_structure": ipo_details.get("share_structure", {}),
                "lockup_period_days": ipo_details.get("lockup_period_days"),
                "insider_shares_pct": ipo_details.get("insider_shares_pct"),
                "float_pct": ipo_details.get("float_pct"),
            },
        }
        return summary

    def _create_analysis_prompt(self, summary: Dict) -> str:
        """Create the analysis prompt for the LLM."""
        prompt = f"""Analyze the risks for the following IPO candidate using ONLY the verified data provided below.

FINANCIAL DATA:
- Revenue: {summary['financials'].get('revenue', 'Not Available')}
- Revenue Growth YoY: {summary['financials'].get('revenue_growth_yoy', 'Not Available')}
- Gross Margin: {summary['financials'].get('gross_margin', 'Not Available')}
- Operating Margin: {summary['financials'].get('operating_margin', 'Not Available')}
- Net Income: {summary['financials'].get('net_income', 'Not Available')}
- EBITDA: {summary['financials'].get('ebitda', 'Not Available')}
- Free Cash Flow: {summary['financials'].get('free_cash_flow', 'Not Available')}
- Cash & Equivalents: {summary['financials'].get('cash_and_equivalents', 'Not Available')}
- Total Debt: {summary['financials'].get('total_debt', 'Not Available')}
- Total Equity: {summary['financials'].get('total_equity', 'Not Available')}
- Debt/Equity: {summary['financials'].get('debt_to_equity', 'Not Available')}
- Current Ratio: {summary['financials'].get('current_ratio', 'Not Available')}
- Quick Ratio: {summary['financials'].get('quick_ratio', 'Not Available')}
- Interest Coverage: {summary['financials'].get('interest_coverage', 'Not Available')}
- Historical Periods: {summary['financials'].get('historical_periods', 0)}

COMPANY PROFILE:
- Key People: {len(summary['company_profile'].get('key_people', []))} identified
- Employee Count: {summary['company_profile'].get('employee_count', 'Not Available')}
- Headquarters: {summary['company_profile'].get('headquarters', 'Not Available')}
- Board Members: {len(summary['company_profile'].get('board_members', []))} identified
- Competitive Advantages: {summary['company_profile'].get('competitive_advantages', [])}

MARKET ANALYSIS:
- TAM Score: {summary['market_analysis'].get('tam_score', 'Not Available')}
- Competitive Intensity: {summary['market_analysis'].get('competitive_intensity', 'Not Available')}
- Moat Strength: {summary['market_analysis'].get('moat_strength', 'Not Available')}
- Total Competitors: {summary['market_analysis'].get('total_comparators', 'Not Available')}
- Direct Competitors: {summary['market_analysis'].get('direct_competitors', 'Not Available')}
- Timing Assessment: {summary['market_analysis'].get('timing_assessment', 'Not Available')}
- Lifecycle: {summary['market_analysis'].get('lifecycle', 'Not Available')}
- CAGR: {summary['market_analysis'].get('cagr', 'Not Available')}
- Tailwinds: {summary['market_analysis'].get('tailwinds', [])}
- Headwinds: {summary['market_analysis'].get('headwinds', [])}

LEGAL DATA:
- Pending Litigation: {len(summary['legal_data'].get('pending_litigation', []))} matters
- Investigations: {len(summary['legal_data'].get('investigations', []))} matters

IPO DETAILS:
- Share Structure: {summary['ipo_details'].get('share_structure', {})}
- Lockup Period: {summary['ipo_details'].get('lockup_period_days', 'Not Available')} days
- Insider Shares: {summary['ipo_details'].get('insider_shares_pct', 'Not Available')}
- Float %: {summary['ipo_details'].get('float_pct', 'Not Available')}

REMEMBER: Use ONLY the data above. If a value says "Not Available", do not guess or infer it. Return null for unavailable data. Distinguish clearly between VERIFIED FACTS (from data above) and YOUR ANALYSIS/INTERPRETATION."""
        return prompt

    def _extract_json(self, content: str) -> Dict:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass
        raise ValueError("Could not extract valid JSON from response")

    def _collect_evidence(self, summary: Dict) -> List[str]:
        evidence = []
        fin = summary.get('financials', {})
        if fin.get('revenue') is not None:
            evidence.append(f"Revenue: {fin['revenue']}")
        if fin.get('revenue_growth_yoy') is not None:
            evidence.append(f"YoY Growth: {fin['revenue_growth_yoy']:.1%}")
        if fin.get('gross_margin') is not None:
            evidence.append(f"Gross Margin: {fin['gross_margin']:.1%}")
        if fin.get('free_cash_flow') is not None:
            evidence.append(f"FCF: {fin['free_cash_flow']}")
        if fin.get('cash_and_equivalents') is not None:
            evidence.append(f"Cash: {fin['cash_and_equivalents']}")
        if fin.get('total_debt') is not None:
            evidence.append(f"Total Debt: {fin['total_debt']}")
        evidence.append(f"Periods analyzed: {fin.get('historical_periods', 0)}")
        return evidence