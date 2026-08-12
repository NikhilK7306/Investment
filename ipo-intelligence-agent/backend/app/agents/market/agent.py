"""Market Analysis Agent - Analyzes market opportunity using LLM."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, DataAvailability
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class TAMAnalysis(BaseModel):
    """Total Addressable Market analysis."""
    score: int = Field(ge=0, le=100)
    tam_usd: Optional[float] = None
    tam_formatted: Optional[str] = None
    cagr: Optional[float] = None
    methodology: Optional[str] = None
    key_drivers: List[str] = []
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class SAMAnalysis(BaseModel):
    """Serviceable Addressable Market analysis."""
    score: int = Field(ge=0, le=100)
    sam_usd: Optional[float] = None
    sam_formatted: Optional[str] = None
    sam_tam_ratio: Optional[float] = None
    methodology: Optional[str] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class SOMAnalysis(BaseModel):
    """Serviceable Obtainable Market analysis."""
    score: int = Field(ge=0, le=100)
    som_usd: Optional[float] = None
    som_formatted: Optional[str] = None
    projected_market_share: Optional[float] = None
    current_revenue: Optional[float] = None
    implied_growth: Optional[float] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class CompetitiveAnalysis(BaseModel):
    """Competitive landscape analysis."""
    score: int = Field(ge=0, le=100)
    total_competitors: Optional[int] = None
    direct_competitors: Optional[int] = None
    indirect_competitors: Optional[int] = None
    public_competitors: Optional[int] = None
    private_competitors: Optional[int] = None
    intensity: Optional[str] = None
    moat_strength: Optional[str] = None
    key_competitors: List[Dict[str, Any]] = []
    market_structure: Optional[str] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class TrendsAnalysis(BaseModel):
    """Market trends and timing analysis."""
    score: int = Field(ge=0, le=100)
    lifecycle: Optional[str] = None
    cagr: Optional[float] = None
    tailwinds: List[str] = []
    headwinds: List[str] = []
    net_sentiment: Optional[str] = None
    timing_assessment: Optional[str] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class PositioningAnalysis(BaseModel):
    """Positioning and differentiation analysis."""
    score: int = Field(ge=0, le=100)
    differentiation: Optional[str] = None
    value_proposition: Optional[str] = None
    switching_costs: Optional[str] = None
    network_effects: Optional[bool] = None
    brand_strength: Optional[str] = None
    advantages: List[str] = []
    positioning_statement: Optional[str] = None
    details: List[str] = []
    metrics: Dict[str, Any] = {}


class MarketAnalysisOutput(BaseModel):
    """Structured output for market analysis."""
    overall_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    tam_analysis: TAMAnalysis
    sam_analysis: SAMAnalysis
    som_analysis: SOMAnalysis
    competitive_analysis: CompetitiveAnalysis
    trends_analysis: TrendsAnalysis
    positioning_analysis: PositioningAnalysis
    market_opportunity_summary: str
    key_risks: List[str]
    key_opportunities: List[str]
    reasoning: str


class MarketAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that analyzes market opportunity using LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.MARKET,
            description="Analyzes market size, growth, competition, and positioning using LLM",
            version="2.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
        self._llm_provider = None

    @property
    def system_prompt(self) -> str:
        return """You are a market research analyst specializing in TAM/SAM/SOM analysis and competitive positioning for IPO candidates.

Analyze the market opportunity for a company going public using this framework:

1. TOTAL ADDRESSABLE MARKET (TAM)
   - Total market demand for the product/service
   - Global vs regional scope
   - Market growth rate (CAGR)
   - Key drivers and tailwinds

2. SERVICEABLE ADDRESSABLE MARKET (SAM)
   - Segment of TAM within company's reach (geography, segment, channels)
   - Realistic capture potential
   - Competitive intensity in SAM

3. SERVICEABLE OBTAINABLE MARKET (SOM)
   - Realistic market share achievable in 3-5 years
   - Go-to-market strategy effectiveness
   - Sales capacity and channel partners

4. COMPETITIVE LANDSCAPE
   - Direct competitors (public and private)
   - Indirect competitors and substitutes
   - Competitive advantages/disadvantages
   - Market share distribution
   - Barriers to entry

5. MARKET TRENDS & DYNAMICS
   - Secular trends (tailwinds/headwinds)
   - Technology disruption
   - Regulatory environment
   - Customer behavior shifts
   - Pricing power dynamics

6. POSITIONING & DIFFERENTIATION
   - Unique value proposition
   - Switching costs
   - Network effects
   - Brand strength
   - IP/patent portfolio

OUTPUT FORMAT:
- TAM/SAM/SOM estimates with methodology
- Market growth rates and drivers
- Competitive map with key players
- Positioning assessment
- Score (0-100) with confidence
- Key risks and opportunities

CRITICAL: Use ONLY the supplied verified data. If information is unavailable, return null/Not Available. Do NOT infer or fabricate factual values. Distinguish clearly between verified facts and your analytical interpretation."""

    @property
    def available_tools(self) -> List[str]:
        return [
            "estimate_tam",
            "estimate_sam",
            "estimate_som",
            "analyze_competitors",
            "get_market_growth_data",
            "analyze_market_trends",
            "assess_barriers_to_entry",
            "evaluate_positioning",
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
            company_profile = input_data.get("company_profile", {})
            industry_data = input_data.get("industry_data", {})
            competitor_data = input_data.get("competitors", [])
            financials = input_data.get("financials", [])

            # Check for critical missing data
            if not company_profile or not company_profile.get("common_name"):
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error="No company profile data provided",
                    error_type="INSUFFICIENT_DATA",
                    data={"data_quality": "none", "reason": "Missing company profile"},
                )

            # Check if industry data is available (not just NOT_AVAILABLE)
            market_cagr = industry_data.get("market_cagr")
            lifecycle = industry_data.get("lifecycle")
            industry_unavailable = (
                market_cagr in (None, "Not Available", DataAvailability.NOT_AVAILABLE.value) and
                lifecycle in (None, "Not Available", DataAvailability.NOT_AVAILABLE.value)
            )
            
            if industry_unavailable and not competitor_data:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error="No market/industry data or competitor data provided",
                    error_type="INSUFFICIENT_DATA",
                    data={"data_quality": "insufficient", "reason": "Missing industry data and competitors"},
                )

            # Get LLM provider
            provider = self._get_llm_provider()
            await provider.initialize()

            # Prepare data summary for LLM
            market_summary = self._prepare_market_summary(
                company_profile, industry_data, competitor_data, financials
            )

            # Create prompt
            prompt = self._create_analysis_prompt(market_summary)

            # Call LLM
            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=4000,
                response_model=MarketAnalysisOutput,
            )

            # Parse response
            if isinstance(response.content, str):
                try:
                    analysis_data = json.loads(response.content)
                except json.JSONDecodeError:
                    analysis_data = self._extract_json(response.content)
            else:
                analysis_data = response.content

            analysis = MarketAnalysisOutput(**analysis_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=analysis.model_dump(),
                confidence=analysis.confidence,
                reasoning=analysis.reasoning,
                evidence=self._collect_evidence(market_summary),
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

    def _prepare_market_summary(
        self,
        company_profile: Dict,
        industry_data: Dict,
        competitor_data: List,
        financials: List,
    ) -> Dict[str, Any]:
        """Prepare verified market data for LLM."""
        
        def safe_get(d: Dict, key: str, default="Not Available"):
            return d.get(key, default)
        
        summary = {
            "company_name": safe_get(company_profile, "common_name", "Unknown"),
            "symbol": safe_get(company_profile, "ticker", "N/A"),
            "sector": safe_get(company_profile, "sector", "Unknown"),
            "industry": safe_get(company_profile, "industry", "Unknown"),
            "business_model": safe_get(company_profile, "business_model", "Not Available"),
            "target_markets": safe_get(company_profile, "target_markets", []),
            "key_products": safe_get(company_profile, "key_products", []),
            "competitive_advantages": safe_get(company_profile, "competitive_advantages", []),
            "differentiation": safe_get(company_profile, "differentiation", "Not Available"),
            "value_proposition": safe_get(company_profile, "value_proposition", "Not Available"),
            "switching_costs": safe_get(company_profile, "switching_costs", "Not Available"),
            "network_effects": safe_get(company_profile, "network_effects", False),
            "brand_strength": safe_get(company_profile, "brand_strength", "Not Available"),
            "tam": safe_get(company_profile, "tam", "Not Available"),
            "industry_data": {
                "market_cagr": safe_get(industry_data, "market_cagr", "Not Available"),
                "lifecycle": safe_get(industry_data, "lifecycle", "Not Available"),
                "tailwinds": safe_get(industry_data, "tailwinds", []),
                "headwinds": safe_get(industry_data, "headwinds", []),
            },
            "competitors": [
                {
                    "name": c.get("name"),
                    "public": c.get("public", False),
                    "estimated_revenue": c.get("revenue"),
                    "differentiation": c.get("differentiation"),
                    "type": c.get("type", "unknown"),
                }
                for c in competitor_data[:10]
            ],
            "financials": financials[0] if financials else {},
        }
        return summary

    def _create_analysis_prompt(self, summary: Dict) -> str:
        """Create the analysis prompt for the LLM."""
        prompt = f"""Analyze the market opportunity for the following IPO candidate using ONLY the verified data provided below.

COMPANY: {summary['company_name']}
Sector: {summary['sector']}
Industry: {summary['industry']}
Business Model: {summary['business_model']}
Target Markets: {', '.join(summary['target_markets']) if summary['target_markets'] else 'Not Available'}
Key Products: {', '.join(summary['key_products']) if summary['key_products'] else 'Not Available'}
Competitive Advantages: {', '.join(summary['competitive_advantages']) if summary['competitive_advantages'] else 'Not Available'}

DIFFERENTIATION & POSITIONING:
- Differentiation: {summary['differentiation']}
- Value Proposition: {summary['value_proposition']}
- Switching Costs: {summary['switching_costs']}
- Network Effects: {summary['network_effects']}
- Brand Strength: {summary['brand_strength']}

COMPETITIVE LANDSCAPE:
{json.dumps(summary['competitors'], indent=2)}

INDUSTRY DATA:
- Market CAGR: {summary['industry_data'].get('market_cagr', 'Not Available')}
- Lifecycle Stage: {summary['industry_data'].get('lifecycle', 'Not Available')}
- Tailwinds: {', '.join(summary['industry_data'].get('tailwinds', [])) if summary['industry_data'].get('tailwinds') else 'Not Available'}
- Headwinds: {', '.join(summary['industry_data'].get('headwinds', [])) if summary['industry_data'].get('headwinds') else 'Not Available'}

TAM (if provided): {summary.get('tam', 'Not Available')}

REMEMBER: Use ONLY the data above. If a value says "Not Available", do not guess or infer it. Return null for unavailable data. Distinguish clearly between VERIFIED FACTS (from data above) and YOUR ANALYSIS/INTERPRETATION."""
        return prompt

    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response."""
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
        if summary.get("tam") != "Not Available":
            evidence.append(f"TAM: {summary['tam']}")
        if summary['industry_data'].get('market_cagr') != "Not Available":
            evidence.append(f"Market CAGR: {summary['industry_data']['market_cagr']}")
        if summary['industry_data'].get('lifecycle') != "Not Available":
            evidence.append(f"Lifecycle: {summary['industry_data']['lifecycle']}")
        if summary['industry_data'].get('tailwinds'):
            evidence.append(f"Tailwinds: {', '.join(summary['industry_data']['tailwinds'][:3])}")
        if summary['competitors']:
            evidence.append(f"Competitors analyzed: {len(summary['competitors'])}")
        return evidence