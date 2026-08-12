"""Fundamental Analysis Agent - Analyzes company financial health using LLM."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus
from app.domain.value_objects.value_objects import FinancialMetrics, ScoreComponent
from app.domain.value_objects.value_objects import Money, Percentage, Ratio
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class RevenueAnalysis(BaseModel):
    """Revenue quality and growth analysis."""
    score: int = Field(ge=0, le=100)
    yoy_growth: Optional[float] = None
    cagr_3y: Optional[float] = None
    gross_margin: Optional[float] = None
    revenue_concentration: Optional[str] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class ProfitabilityAnalysis(BaseModel):
    """Profitability analysis."""
    score: int = Field(ge=0, le=100)
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class BalanceSheetAnalysis(BaseModel):
    """Balance sheet strength analysis."""
    score: int = Field(ge=0, le=100)
    cash_position: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class CashFlowAnalysis(BaseModel):
    """Cash flow quality analysis."""
    score: int = Field(ge=0, le=100)
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    fcf_margin: Optional[float] = None
    fcf_conversion: Optional[float] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class ValuationAnalysis(BaseModel):
    """Valuation analysis."""
    score: int = Field(ge=0, le=100)
    ev_revenue: Optional[float] = None
    ev_ebitda: Optional[float] = None
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    vs_peers: Optional[str] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class GrowthAnalysis(BaseModel):
    """Growth sustainability analysis."""
    score: int = Field(ge=0, le=100)
    tam_usd: Optional[float] = None
    competitive_advantages: List[str] = []
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class FundamentalAnalysisOutput(BaseModel):
    """Structured output for fundamental analysis."""
    overall_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    revenue_analysis: RevenueAnalysis
    profitability_analysis: ProfitabilityAnalysis
    balance_sheet_analysis: BalanceSheetAnalysis
    cash_flow_analysis: CashFlowAnalysis
    valuation_analysis: ValuationAnalysis
    growth_analysis: GrowthAnalysis
    key_metrics: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    red_flags: List[str]
    public_comps: List[Dict[str, Any]] = []
    reasoning: str


class FundamentalAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that performs fundamental financial analysis using LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.FUNDAMENTAL,
            description="Analyzes company financial health, profitability, and growth using LLM",
            version="2.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
        self._llm_provider = None

    @property
    def system_prompt(self) -> str:
        return """You are a senior equity research analyst specializing in fundamental analysis of pre-IPO companies.

Your task is to analyze the financial health and quality of a company preparing for IPO.

ANALYSIS FRAMEWORK:
1. REVENUE QUALITY & GROWTH
   - Revenue trends (YoY, QoQ, CAGR)
   - Revenue concentration/diversification
   - Recurring vs one-time revenue
   - Geographic diversification

2. PROFITABILITY
   - Gross margin trends and sustainability
   - Operating leverage
   - Net income trajectory
   - Unit economics (LTV/CAC, payback period)

3. BALANCE SHEET STRENGTH
   - Cash position and runway
   - Debt levels and maturity profile
   - Working capital management
   - Asset quality

4. CASH FLOW
   - Operating cash flow consistency
   - Free cash flow generation
   - Capex requirements
   - FCF conversion rate

5. VALUATION METRICS
   - Revenue multiples (EV/Revenue)
   - EBITDA multiples
   - Growth-adjusted metrics (PEG)
   - Comparison to public comps

6. GROWTH SUSTAINABILITY
   - TAM/SAM/SOM analysis
   - Competitive moat
   - Market share trajectory
   - Expansion opportunities

OUTPUT FORMAT:
Provide a structured analysis with:
- Overall score (0-100)
- Confidence level (0-1)
- Detailed reasoning for each pillar
- Key strengths and weaknesses
- Specific financial metrics with interpretation
- Red flags or concerns
- Comparison to relevant public comps

CRITICAL: Use ONLY the supplied verified data. If information is unavailable, return null/Not Available. Do NOT infer or fabricate factual values. Distinguish clearly between verified facts and your analytical interpretation."""

    @property
    def available_tools(self) -> List[str]:
        return [
            "get_financial_statements",
            "calculate_ratios",
            "get_public_comps",
            "analyze_revenue_quality",
            "assess_profitability",
            "evaluate_balance_sheet",
            "analyze_cash_flows",
            "compute_valuation_multiples",
        ]

    def _get_llm_provider(self):
        """Get or create LLM provider."""
        if self._llm_provider is None:
            self._llm_provider = LLMProviderFactory.create_from_env()
        return self._llm_provider

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute fundamental analysis using LLM."""
        start_time = datetime.utcnow()

        try:
            # Extract input data
            financials = input_data.get("financials", [])
            company_profile = input_data.get("company_profile", {})
            public_comps = input_data.get("public_comps", [])

            if not financials:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error="No verified financial data provided",
                    error_type="INSUFFICIENT_DATA",
                    data={"data_quality": "none", "reason": "No financial statements available"},
                )

            # Prepare data for LLM
            latest = financials[0] if financials else {}
            financial_summary = self._prepare_financial_summary(latest, financials, company_profile, public_comps)

            # Get LLM provider
            provider = self._get_llm_provider()
            await provider.initialize()

            # Create prompt for LLM
            prompt = self._create_analysis_prompt(financial_summary)

            # Call LLM with structured output
            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=4000,
                response_model=FundamentalAnalysisOutput,
            )

            # Parse response
            if isinstance(response.content, str):
                try:
                    analysis_data = json.loads(response.content)
                except json.JSONDecodeError:
                    # Try to extract JSON from content
                    analysis_data = self._extract_json(response.content)
            else:
                analysis_data = response.content

            # Validate and ensure required fields
            analysis = FundamentalAnalysisOutput(**analysis_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=analysis.model_dump(),
                confidence=analysis.confidence,
                reasoning=analysis.reasoning,
                evidence=self._collect_evidence(financial_summary),
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

    def _prepare_financial_summary(
        self,
        latest: Dict,
        financials: List[Dict],
        company_profile: Dict,
        public_comps: List[Dict],
    ) -> Dict[str, Any]:
        """Prepare verified financial data for LLM analysis."""
        
        def safe_get(d: Dict, key: str, default=None):
            return d.get(key, default)
        
        def fmt_money(val, currency="USD"):
            if val is None:
                return "Not Available"
            return f"{currency} {val:,.0f}"
        
        def fmt_pct(val):
            if val is None:
                return "Not Available"
            return f"{val:.1%}"
        
        def fmt_ratio(val):
            if val is None:
                return "Not Available"
            return f"{val:.2f}x"

        summary = {
            "company_name": company_profile.get("common_name", "Unknown"),
            "symbol": company_profile.get("ticker", "N/A"),
            "exchange": company_profile.get("exchange", "N/A"),
            "sector": company_profile.get("sector", "N/A"),
            "industry": company_profile.get("industry", "N/A"),
            "description": company_profile.get("description", "Not Available"),
            "business_model": company_profile.get("business_model", "Not Available"),
            "verified_financials": {
                "latest_period": latest.get("period_end", "Not Available"),
                "revenue": fmt_money(safe_get(latest, "revenue")),
                "revenue_growth_yoy": fmt_pct(safe_get(latest, "revenue_growth_yoy")),
                "revenue_growth_qoq": fmt_pct(safe_get(latest, "revenue_growth_qoq")),
                "gross_profit": fmt_money(safe_get(latest, "gross_profit")),
                "gross_margin": fmt_pct(safe_get(latest, "gross_margin")),
                "operating_income": fmt_money(safe_get(latest, "operating_income")),
                "operating_margin": fmt_pct(safe_get(latest, "operating_margin")),
                "net_income": fmt_money(safe_get(latest, "net_income")),
                "net_margin": fmt_pct(safe_get(latest, "net_margin")),
                "ebitda": fmt_money(safe_get(latest, "ebitda")),
                "ebitda_margin": fmt_pct(safe_get(latest, "ebitda_margin")),
                "free_cash_flow": fmt_money(safe_get(latest, "free_cash_flow")),
                "fcf_margin": fmt_pct(safe_get(latest, "fcf_margin")),
                "cash_and_equivalents": fmt_money(safe_get(latest, "cash_and_equivalents")),
                "total_debt": fmt_money(safe_get(latest, "total_debt")),
                "total_equity": fmt_money(safe_get(latest, "total_equity")),
                "debt_to_equity": fmt_ratio(safe_get(latest, "debt_to_equity")),
                "current_ratio": fmt_ratio(safe_get(latest, "current_ratio")),
                "quick_ratio": fmt_ratio(safe_get(latest, "quick_ratio")),
                "roe": fmt_pct(safe_get(latest, "roe")),
                "roic": fmt_pct(safe_get(latest, "roic")),
            },
            "historical_periods": len(financials),
            "public_comps": [
                {
                    "symbol": c.get("symbol"),
                    "name": c.get("name"),
                    "market_cap": fmt_money(c.get("market_cap")) if c.get("market_cap") else "N/A",
                    "ev_revenue": fmt_ratio(c.get("ev_revenue")),
                    "ev_ebitda": fmt_ratio(c.get("ev_ebitda")),
                    "pe_ratio": fmt_ratio(c.get("pe_ratio")),
                    "revenue_growth": fmt_pct(c.get("revenue_growth")),
                    "profit_margin": fmt_pct(c.get("profit_margin")),
                }
                for c in public_comps[:5]
            ],
            "company_info": {
                "employees": company_profile.get("employees", "N/A"),
                "headquarters": company_profile.get("headquarters", "N/A"),
                "ceo": company_profile.get("ceo", "N/A"),
                "website": company_profile.get("website", "N/A"),
            },
        }
        return summary

    def _create_analysis_prompt(self, summary: Dict) -> str:
        """Create the analysis prompt for the LLM."""
        financials = summary["verified_financials"]
        comps = summary["public_comps"]
        
        prompt = f"""Analyze the following IPO candidate using ONLY the verified data provided below.

COMPANY: {summary['company_name']} ({summary['symbol']})
Exchange: {summary['exchange']}
Sector: {summary['sector']}
Industry: {summary['industry']}
Description: {summary['description']}
Business Model: {summary['business_model']}

VERIFIED FINANCIAL DATA (Latest Period: {financials.get('latest_period', 'N/A')}):
- Revenue: {financials.get('revenue')}
- YoY Growth: {financials.get('revenue_growth_yoy')}
- QoQ Growth: {financials.get('revenue_growth_qoq')}
- Gross Profit: {financials.get('gross_profit')}
- Gross Margin: {financials.get('gross_margin')}
- Operating Income: {financials.get('operating_income')}
- Operating Margin: {financials.get('operating_margin')}
- Net Income: {financials.get('net_income')}
- Net Margin: {financials.get('net_margin')}
- EBITDA: {financials.get('ebitda')}
- EBITDA Margin: {financials.get('ebitda_margin')}
- Free Cash Flow: {financials.get('free_cash_flow')}
- FCF Margin: {financials.get('fcf_margin')}
- Cash & Equivalents: {financials.get('cash_and_equivalents')}
- Total Debt: {financials.get('total_debt')}
- Total Equity: {financials.get('total_equity')}
- Debt/Equity: {financials.get('debt_to_equity')}
- Current Ratio: {financials.get('current_ratio')}
- Quick Ratio: {financials.get('quick_ratio')}
- ROE: {financials.get('roe')}
- ROIC: {financials.get('roic')}

HISTORICAL DATA: {summary['historical_periods']} periods available

PUBLIC COMPARABLES:
{json.dumps(comps, indent=2)}

COMPANY INFO:
- Employees: {summary['company_info'].get('employees')}
- HQ: {summary['company_info'].get('headquarters')}
- CEO: {summary['company_info'].get('ceo')}

REMEMBER: Use ONLY the data above. If a value says "Not Available", do not guess or infer it. Return null for unavailable data. Distinguish between VERIFIED FACTS (from data above) and YOUR ANALYSIS/INTERPRETATION."""
        return prompt

    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass
        raise ValueError("Could not extract valid JSON from response")

    def _collect_evidence(self, summary: Dict) -> List[str]:
        """Collect evidence citations from verified data."""
        financials = summary["verified_financials"]
        evidence = []
        
        if financials.get("revenue") != "Not Available":
            evidence.append(f"Revenue: {financials['revenue']}")
        if financials.get("revenue_growth_yoy") != "Not Available":
            evidence.append(f"YoY Growth: {financials['revenue_growth_yoy']}")
        if financials.get("gross_margin") != "Not Available":
            evidence.append(f"Gross Margin: {financials['gross_margin']}")
        if financials.get("operating_margin") != "Not Available":
            evidence.append(f"Operating Margin: {financials['operating_margin']}")
        if financials.get("free_cash_flow") != "Not Available":
            evidence.append(f"FCF: {financials['free_cash_flow']}")
        if financials.get("cash_and_equivalents") != "Not Available":
            evidence.append(f"Cash: {financials['cash_and_equivalents']}")
        if financials.get("total_debt") != "Not Available":
            evidence.append(f"Total Debt: {financials['total_debt']}")
        
        evidence.append(f"Periods analyzed: {summary['historical_periods']}")
        evidence.append(f"Public comps: {len(summary['public_comps'])}")
        
        return evidence