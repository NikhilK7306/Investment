"""Report Generation Agent - Creates comprehensive investment research reports using LLM."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, InvestmentStrategy, RiskLevel, TimeHorizon
from app.domain.entities.entities import OverallAnalysis, Report
from app.domain.value_objects.value_objects import InvestmentThesis, Money, Percentage
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class ReportOutput(BaseModel):
    """Structured output for report generation."""
    title: str
    executive_summary: str
    ipo_overview: str
    company_background: str
    industry_analysis: str
    financial_analysis: str
    valuation_analysis: str
    risk_analysis: str
    management_assessment: str
    sentiment_analysis: str
    bull_case: str
    bear_case: str
    investment_thesis: str
    recommendation: str
    key_metrics: Dict[str, Any]
    financial_tables: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    disclaimers: List[str]
    reasoning: str
    confidence: float = Field(ge=0, le=1)


class ReportGenerationAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that generates professional investment research reports using LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.REPORT,
            description="Generates comprehensive investment research reports from analysis results using LLM",
            version="2.0.0",
            max_retries=1,
            timeout_seconds=180,
        )
        self._llm_provider = None

    @property
    def system_prompt(self) -> str:
        return """You are a senior equity research report writer producing institutional-quality IPO research reports.

Your reports must be:
- Objective, balanced, and evidence-based
- Clear about bull and bear cases
- Transparent about assumptions and limitations
- Professional in tone and formatting
- Actionable with clear recommendations

REPORT STRUCTURE:
1. EXECUTIVE SUMMARY
   - One-page summary with key findings
   - Investment recommendation and rationale
   - Overall score and confidence

2. IPO OVERVIEW
   - Company background and business model
   - IPO terms and structure
   - Use of proceeds
   - Lockup and ownership structure

3. COMPANY BACKGROUND
   - History and milestones
   - Products/services and revenue model
   - Target markets and customers
   - Competitive advantages

4. INDUSTRY ANALYSIS
   - Market size (TAM/SAM/SOM)
   - Growth drivers and trends
   - Competitive landscape
   - Regulatory environment

5. FINANCIAL ANALYSIS
   - Historical financials (3-5 years)
   - Key metrics and ratios
   - Margin trends and drivers
   - Cash flow and balance sheet
   - Comparison to public peers

6. VALUATION ANALYSIS
   - DCF valuation with assumptions
   - Comparable company analysis
   - Precedent transaction analysis
   - IPO valuation vs. peers
   - Sensitivity analysis

7. RISK ANALYSIS
   - Top 10 risks ranked by severity
   - Financial, market, operational, regulatory
   - Post-IPO specific risks
   - Mitigation factors

8. MANAGEMENT ASSESSMENT
   - Leadership team experience
   - Board composition and independence
   - Governance structure
   - Insider ownership and alignment

9. SENTIMENT ANALYSIS
   - News and media sentiment
   - Analyst expectations
   - Social media sentiment
   - Institutional interest

10. INVESTMENT THESIS
    - Bull case with key drivers
    - Bear case with key risks
    - Probability-weighted scenarios
    - Catalyst timeline

11. RECOMMENDATION
    - Final score (0-100)
    - Investment strategy
    - Time horizon
    - Position sizing guidance
    - Entry strategy
    - Monitoring plan

12. APPENDICES
    - Detailed financial tables
    - Glossary
    - Disclaimers
    - Source references

WRITING GUIDELINES:
- Use specific numbers, not vague descriptions
- Cite sources for all key claims
- Present both sides fairly
- Quantify uncertainty where possible
- Avoid promotional language
- Include standard disclaimers
- CRITICAL: Use ONLY the supplied verified analyses. Do NOT invent new data. Clearly distinguish between VERIFIED FACTS (from agent analyses) and YOUR SYNTHESIS/INTERPRETATION."""

    @property
    def available_tools(self) -> List[str]:
        return [
            "render_executive_summary",
            "render_ipo_overview",
            "render_company_background",
            "render_industry_analysis",
            "render_financial_analysis",
            "render_valuation_analysis",
            "render_risk_analysis",
            "render_management_assessment",
            "render_sentiment_analysis",
            "render_investment_thesis",
            "render_recommendation",
            "generate_pdf",
            "generate_html",
            "generate_markdown",
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
            overall_analysis = input_data.get("overall_analysis", {})
            fundamental = input_data.get("fundamental_analysis", {})
            market = input_data.get("market_analysis", {})
            risk = input_data.get("risk_analysis", {})
            sentiment = input_data.get("sentiment_analysis", {})
            ipo_details = input_data.get("ipo_details", {})
            company_profile = input_data.get("company_profile", {})
            financials = input_data.get("financials", {})
            public_comps = input_data.get("public_comps", [])

            symbol = context.ipo_symbol
            analysis_id = context.analysis_id

            provider = self._get_llm_provider()
            await provider.initialize()

            report_summary = self._prepare_report_summary(
                overall_analysis, fundamental, market, risk, sentiment,
                ipo_details, company_profile, financials, public_comps
            )

            prompt = self._create_report_prompt(report_summary, symbol, overall_analysis)

            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=8000,
                response_model=ReportOutput,
            )

            if isinstance(response.content, str):
                try:
                    report_data = json.loads(response.content)
                except json.JSONDecodeError:
                    report_data = self._extract_json(response.content)
            else:
                report_data = response.content

            report = ReportOutput(**report_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data={
                    "report": report.model_dump(),
                    "markdown": self._generate_markdown(report, symbol, overall_analysis),
                    "key_metrics": report.key_metrics,
                    "financial_tables": report.financial_tables,
                    "charts": report.charts,
                    "sources": report.sources,
                },
                confidence=report.confidence,
                reasoning=report.reasoning,
                evidence=self._collect_evidence(report_summary),
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

    def _prepare_report_summary(
        self,
        overall: Dict,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
        ipo_details: Dict,
        company_profile: Dict,
        financials: Dict,
        public_comps: List,
    ) -> Dict[str, Any]:
        """Prepare verified data for report generation."""
        
        def safe_get(d: Dict, key: str, default="Not Available"):
            return d.get(key, default)
        
        def fmt_money(val, currency="USD"):
            if val is None or val == "Not Available":
                return "N/A"
            try:
                return f"{currency} {float(val):,.0f}"
            except (ValueError, TypeError):
                return str(val)
        
        def fmt_pct(val):
            if val is None or val == "Not Available":
                return "N/A"
            try:
                return f"{float(val):.1%}"
            except (ValueError, TypeError):
                return str(val)

        summary = {
            "symbol": safe_get(ipo_details, "symbol", "N/A"),
            "company_name": safe_get(ipo_details, "company_name", "N/A"),
            "exchange": safe_get(ipo_details, "exchange", "N/A"),
            "sector": safe_get(company_profile, "sector", "N/A"),
            "industry": safe_get(company_profile, "industry", "N/A"),
            "expected_date": safe_get(ipo_details, "expected_date", "TBD"),
            "price_range": safe_get(ipo_details, "price_range", "Not disclosed"),
            "shares_offered": safe_get(ipo_details, "shares_offered", "TBD"),
            "valuation": safe_get(ipo_details, "valuation", {}),
            "underwriters": safe_get(ipo_details, "underwriters", []),
            "lockup_days": safe_get(ipo_details, "lockup_period_days", "N/A"),
            "use_of_proceeds": safe_get(ipo_details, "use_of_proceeds", "General corporate purposes"),
            
            "overall": {
                "overall_score": safe_get(overall, "overall_score", 0),
                "confidence": safe_get(overall, "confidence", 0),
                "recommendation": safe_get(overall, "investment_strategy", "WATCH"),
                "risk_level": safe_get(overall, "risk_level", "MODERATE"),
                "time_horizon": safe_get(overall, "time_horizon", "MEDIUM_TERM"),
                "financial_strength_score": safe_get(overall, "financial_strength_score", 0),
                "growth_potential_score": safe_get(overall, "growth_potential_score", 0),
                "market_opportunity_score": safe_get(overall, "market_opportunity_score", 0),
                "management_quality_score": safe_get(overall, "management_quality_score", 0),
                "risk_level_score": safe_get(overall, "risk_level_score", 0),
                "bull_case": safe_get(overall, "bull_case", "Not generated"),
                "bear_case": safe_get(overall, "bear_case", "Not generated"),
                "key_risks": safe_get(overall, "key_risks", []),
                "key_catalysts": safe_get(overall, "key_catalysts", []),
            },
            
            "fundamental": {
                "overall_score": safe_get(fundamental, "overall_score", 0),
                "confidence": safe_get(fundamental, "confidence", 0),
                "strengths": safe_get(fundamental, "strengths", []),
                "weaknesses": safe_get(fundamental, "weaknesses", []),
                "red_flags": safe_get(fundamental, "red_flags", []),
                "key_metrics": safe_get(fundamental, "key_metrics", {}),
                "pillar_scores": safe_get(fundamental, "pillar_scores", {}),
            },
            
            "market": {
                "overall_score": safe_get(market, "overall_score", 0),
                "confidence": safe_get(market, "confidence", 0),
                "tam_analysis": safe_get(market, "tam_analysis", {}),
                "sam_analysis": safe_get(market, "sam_analysis", {}),
                "som_analysis": safe_get(market, "som_analysis", {}),
                "competitive_analysis": safe_get(market, "competitive_analysis", {}),
                "trends_analysis": safe_get(market, "trends_analysis", {}),
                "positioning_analysis": safe_get(market, "positioning_analysis", {}),
                "key_opportunities": safe_get(market, "key_opportunities", []),
                "key_risks": safe_get(market, "key_risks", []),
            },
            
            "risk": {
                "overall_risk_score": safe_get(risk, "overall_risk_score", 50),
                "confidence": safe_get(risk, "confidence", 0.5),
                "overall_risk_level": safe_get(risk, "overall_risk_level", "MODERATE"),
                "high_priority_risks": safe_get(risk, "high_priority_risks", 0),
                "top_risks": safe_get(risk, "top_risks", [])[:10],
                "red_flags": safe_get(risk, "red_flags", []),
                "risk_by_category": safe_get(risk, "risk_by_category", {}),
                "scenarios": safe_get(risk, "scenarios", {}),
            },
            
            "sentiment": {
                "composite_score": safe_get(sentiment, "composite_score", 0),
                "composite_label": safe_get(sentiment, "composite_label", "NEUTRAL"),
                "confidence": safe_get(sentiment, "confidence", 0.5),
                "source_breakdown": safe_get(sentiment, "source_breakdown", {}),
                "positive_themes": safe_get(sentiment, "positive_themes", []),
                "negative_themes": safe_get(sentiment, "negative_themes", []),
                "divergences": safe_get(sentiment, "divergences", []),
                "momentum": safe_get(sentiment, "momentum", "stable"),
            },
            
            "financials": {
                "statements": safe_get(financials, "statements", []),
            },
            
            "public_comps": public_comps,
            
            "company_profile": {
                "legal_name": safe_get(company_profile, "legal_name", ""),
                "description": safe_get(company_profile, "description", ""),
                "business_model": safe_get(company_profile, "business_model", ""),
                "competitive_advantages": safe_get(company_profile, "competitive_advantages", []),
                "key_products": safe_get(company_profile, "key_products", []),
                "target_markets": safe_get(company_profile, "target_markets", []),
                "ceo": safe_get(company_profile, "ceo", ""),
                "cfo": safe_get(company_profile, "cfo", ""),
                "coo": safe_get(company_profile, "coo", ""),
                "board_members": safe_get(company_profile, "board_members", []),
                "founded_year": safe_get(company_profile, "founded_year", "N/A"),
                "employee_count": safe_get(company_profile, "employee_count", "N/A"),
                "website": safe_get(company_profile, "website", ""),
                "headquarters": safe_get(company_profile, "headquarters", "N/A"),
            },
        }
        return summary

    def _create_report_prompt(self, summary: Dict, symbol: str, overall: Dict) -> str:
        """Create the report generation prompt for the LLM."""
        overall_data = summary["overall"]
        fundamental = summary["fundamental"]
        market = summary["market"]
        risk = summary["risk"]
        sentiment = summary["sentiment"]
        ipo = {k: v for k, v in summary.items() if k not in ["overall", "fundamental", "market", "risk", "sentiment", "financials", "public_comps", "company_profile"]}
        
        prompt = f"""Generate a comprehensive institutional-quality IPO investment research report for {summary['company_name']} ({symbol}).

OVERALL ASSESSMENT:
- Overall Score: {overall_data['overall_score']}/100
- Confidence: {overall_data['confidence']:.0%}
- Recommendation: {overall_data['recommendation']}
- Risk Level: {overall_data['risk_level']}
- Time Horizon: {overall_data['time_horizon']}

VERIFIED IPO DETAILS:
- Exchange: {ipo['exchange']}
- Expected Date: {ipo['expected_date']}
- Price Range: {ipo['price_range']}
- Shares Offered: {ipo['shares_offered']}
- Valuation: {json.dumps(ipo['valuation'], indent=2)}
- Lead Underwriters: {', '.join(ipo['underwriters']) if ipo['underwriters'] else 'TBD'}
- Lockup Period: {ipo['lockup_days']} days
- Use of Proceeds: {ipo['use_of_proceeds']}

FUNDAMENTAL ANALYSIS (Score: {fundamental['overall_score']}/100, Confidence: {fundamental['confidence']:.0%}):
- Strengths: {fundamental['strengths']}
- Weaknesses: {fundamental['weaknesses']}
- Red Flags: {fundamental['red_flags']}
- Key Metrics: {json.dumps(fundamental['key_metrics'], indent=2)}

MARKET ANALYSIS (Score: {market['overall_score']}/100, Confidence: {market['confidence']:.0%}):
- TAM: {json.dumps(market['tam_analysis'], indent=2)}
- SAM: {json.dumps(market['sam_analysis'], indent=2)}
- SOM: {json.dumps(market['som_analysis'], indent=2)}
- Competitive Landscape: {json.dumps(market['competitive_analysis'], indent=2)}
- Key Opportunities: {market['key_opportunities']}
- Key Risks: {market['key_risks']}

RISK ANALYSIS (Risk Score: {risk['overall_risk_score']}/100, Confidence: {risk['confidence']:.0%}):
- Overall Risk Level: {risk['overall_risk_level']}
- High Priority Risks: {risk['high_priority_risks']}
- Top Risks: {json.dumps(risk['top_risks'], indent=2)}
- Red Flags: {risk['red_flags']}
- Scenarios: {json.dumps(risk['scenarios'], indent=2)}

SENTIMENT ANALYSIS (Score: {sentiment['composite_score']:.2f}, Label: {sentiment['composite_label']}, Confidence: {sentiment['confidence']:.0%}):
- Positive Themes: {sentiment['positive_themes']}
- Negative Themes: {sentiment['negative_themes']}
- Divergences: {sentiment['divergences']}
- Momentum: {sentiment['momentum']}

OVERALL INVESTMENT THESIS:
- Bull Case: {overall['bull_case']}
- Bear Case: {overall['bear_case']}
- Key Risks: {overall['key_risks']}
- Key Catalysts: {overall['key_catalysts']}

REMEMBER: Use ONLY the verified data above. Do NOT invent new data. Clearly distinguish between VERIFIED FACTS (from the analyses above) and YOUR SYNTHESIS/INTERPRETATION. Include all 12 report sections with professional formatting. Add standard disclaimers."""
        return prompt

    def _generate_markdown(self, report: ReportOutput, symbol: str, overall: Dict) -> str:
        """Generate markdown version of the report."""
        parts = [
            f"# {report.title}",
            "",
            f"**Date:** {datetime.utcnow().strftime('%B %d, %Y')}",
            f"**Analyst:** IPO Intelligence Agent",
            f"**Recommendation:** {overall.get('investment_strategy', 'WATCH')} | **Score:** {overall.get('overall_score', 0):.1f}/100",
            f"**Confidence:** {overall.get('confidence', 0):.0%} | **Risk:** {overall.get('risk_level', 'MODERATE')}",
            "",
            "---",
            "",
        ]

        sections = [
            ("executive_summary", "Executive Summary"),
            ("ipo_overview", "IPO Overview"),
            ("company_background", "Company Background"),
            ("industry_analysis", "Industry Analysis"),
            ("financial_analysis", "Financial Analysis"),
            ("valuation_analysis", "Valuation Analysis"),
            ("risk_analysis", "Risk Analysis"),
            ("management_assessment", "Management Assessment"),
            ("sentiment_analysis", "Sentiment Analysis"),
            ("investment_thesis", "Investment Thesis"),
            ("recommendation", "Recommendation"),
        ]

        for key, title in sections:
            content = getattr(report, key, "")
            if content:
                parts.append(f"## {title}")
                parts.append("")
                parts.append(content)
                parts.append("")
                parts.append("---")
                parts.append("")

        # Add disclaimers
        if report.disclaimers:
            parts.append("## Disclaimers")
            parts.append("")
            for disclaimer in report.disclaimers:
                parts.append(f"- {disclaimer}")
            parts.append("")

        return "\n".join(parts)

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
        for key in ["overall", "fundamental", "market", "risk", "sentiment"]:
            data = summary.get(key, {})
            if data.get("overall_score") is not None:
                evidence.append(f"{key}: Score={data['overall_score']:.1f}, Conf={data.get('confidence', 0):.0%}")
        return evidence