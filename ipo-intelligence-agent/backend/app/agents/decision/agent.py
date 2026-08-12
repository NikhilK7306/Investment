"""Decision Support Agent - Synthesizes all analyses into final recommendation using LLM."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, InvestmentStrategy, RiskLevel, TimeHorizon
from app.domain.entities.entities import OverallAnalysis
from app.domain.value_objects.value_objects import InvestmentThesis, Money, Percentage
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class DecisionAnalysisOutput(BaseModel):
    """Structured output for decision synthesis."""
    overall_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    recommendation: str
    risk_level: str
    time_horizon: str
    pillar_scores: Dict[str, float]
    weights_used: Dict[str, float]
    investment_thesis: Dict[str, Any]
    position_guidance: Dict[str, Any]
    entry_strategy: Dict[str, Any]
    monitoring_plan: Dict[str, Any]
    scenario_analysis: Dict[str, Any]
    reasoning: str
    positive_factors: List[str]
    negative_factors: List[str]
    key_risks: List[str]
    key_catalysts: List[str]
    valuation_concerns: List[str]
    financial_concerns: List[str]
    market_conditions: List[str]
    data_limitations: List[str]


class DecisionSupportAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that synthesizes all analyses into final investment decision using LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.DECISION,
            description="Synthesizes all agent analyses into final investment recommendation using LLM",
            version="2.0.0",
            max_retries=1,
            timeout_seconds=120,
        )
        self._llm_provider = None
        
        # Default scoring weights
        self.weights = {
            "fundamental": 0.25,
            "market": 0.20,
            "risk": 0.15,  # Inverted
            "sentiment": 0.10,
            "management": 0.15,
            "valuation": 0.15,
        }

    @property
    def system_prompt(self) -> str:
        return """You are the Chief Investment Officer synthesizing research from multiple analysts.

Your task is to produce a final investment recommendation by weighing all analyses.

SYNTHESIS FRAMEWORK:

1. SCORE AGGREGATION
   - Weight each pillar by importance
   - Risk score is inverted (lower risk = higher score)
   - Apply confidence adjustments
   - Calculate overall 0-100 score

2. INVESTMENT THESIS
   - Clear bull case with key drivers
   - Clear bear case with key risks
   - Probability-weighted scenarios
   - Time horizon for each scenario

3. RECOMMENDATION MAPPING
   - 90-100: Aggressive Buy (Exceptional)
   - 70-89: Buy (Strong)
   - 55-69: Accumulate (Moderate)
   - 45-54: Hold (Neutral)
   - 35-44: Watch (Monitor)
   - 25-34: Reduce (Cautious)
   - 15-24: Sell (Negative)
   - 0-14: Avoid (Very Negative)

4. POSITION SIZING GUIDANCE
   - Based on conviction, risk, liquidity
   - Max position size suggestions
   - Entry strategy (staged vs lump sum)

5. RISK MANAGEMENT
   - Stop-loss levels
   - Key monitoring metrics
   - Catalyst calendar
   - Contingency plans

OUTPUT:
- Overall score and recommendation
- Detailed investment thesis
- Position sizing guidance
- Risk management framework
- Monitoring checklist
- Confidence and uncertainty quantification

CRITICAL: Use ONLY the supplied verified analyses. Do NOT invent new data. Clearly distinguish between VERIFIED FACTS (from agent analyses) and YOUR SYNTHESIS/INTERPRETATION. AI recommendations must NOT be presented as guaranteed outcomes. Include confidence, uncertainty, and data limitations."""

    @property
    def available_tools(self) -> List[str]:
        return [
            "calculate_weighted_score",
            "generate_bull_bear_cases",
            "determine_recommendation",
            "calculate_position_size",
            "create_monitoring_plan",
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
            fundamental = input_data.get("fundamental_analysis", {})
            market = input_data.get("market_analysis", {})
            risk = input_data.get("risk_analysis", {})
            sentiment = input_data.get("sentiment_analysis", {})

            # ============================================================
            # VALIDATE UPSTREAM AGENT DATA QUALITY
            # ============================================================
            # Check if we have sufficient data from upstream agents
            upstream_agents = {
                "fundamental": fundamental,
                "market": market,
                "risk": risk,
                "sentiment": sentiment,
            }
            
            sufficient_count = 0
            for name, data in upstream_agents.items():
                # Check if agent completed successfully with data
                agent_status = data.get("agent_status", "unknown")
                data_quality = data.get("data_quality", "unknown")
                if agent_status == "completed" and data_quality == "sufficient":
                    sufficient_count += 1
            
            if sufficient_count < 2:
                # Need at least 2 agents with sufficient data
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error=f"Insufficient upstream data: only {sufficient_count}/4 agents have sufficient data",
                    error_type="INSUFFICIENT_DATA",
                    data={
                        "data_quality": "insufficient",
                        "reason": "Not enough upstream agents with verified data",
                        "upstream_status": {k: v.get("agent_status", "unknown") for k, v in upstream_agents.items()},
                    },
                )

            provider = self._get_llm_provider()
            await provider.initialize()

            decision_summary = self._prepare_decision_summary(
                fundamental, market, risk, sentiment
            )

            prompt = self._create_analysis_prompt(decision_summary)

            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=4000,
                response_model=DecisionAnalysisOutput,
            )

            if isinstance(response.content, str):
                try:
                    analysis_data = json.loads(response.content)
                except json.JSONDecodeError:
                    analysis_data = self._extract_json(response.content)
            else:
                analysis_data = response.content

            analysis = DecisionAnalysisOutput(**analysis_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=analysis.model_dump(),
                confidence=analysis.confidence,
                reasoning=analysis.reasoning,
                evidence=self._collect_evidence(decision_summary),
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

    def _prepare_decision_summary(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
    ) -> Dict[str, Any]:
        """Prepare verified analysis data for decision synthesis."""
        
        def safe_get(d: Dict, key: str, default=None):
            return d.get(key, default)
        
        summary = {
            "fundamental": {
                "overall_score": safe_get(fundamental, "overall_score", 50),
                "confidence": safe_get(fundamental, "confidence", 0.5),
                "strengths": safe_get(fundamental, "strengths", []),
                "weaknesses": safe_get(fundamental, "weaknesses", []),
                "red_flags": safe_get(fundamental, "red_flags", []),
                "key_metrics": safe_get(fundamental, "key_metrics", {}),
                "pillar_scores": safe_get(fundamental, "pillar_scores", {}),
                "data_quality": safe_get(fundamental, "data_quality", "unknown"),
                "agent_status": safe_get(fundamental, "agent_status", "unknown"),
            },
            "market": {
                "overall_score": safe_get(market, "overall_score", 50),
                "confidence": safe_get(market, "confidence", 0.5),
                "market_opportunity_summary": safe_get(market, "market_opportunity_summary", ""),
                "key_opportunities": safe_get(market, "key_opportunities", []),
                "key_risks": safe_get(market, "key_risks", []),
                "tam_analysis": safe_get(market, "tam_analysis", {}),
                "competitive_analysis": safe_get(market, "competitive_analysis", {}),
                "positioning_analysis": safe_get(market, "positioning_analysis", {}),
                "data_quality": safe_get(market, "data_quality", "unknown"),
                "agent_status": safe_get(market, "agent_status", "unknown"),
            },
            "risk": {
                "overall_risk_score": safe_get(risk, "overall_risk_score", 50),
                "confidence": safe_get(risk, "confidence", 0.5),
                "overall_risk_level": safe_get(risk, "overall_risk_level", "MODERATE"),
                "high_priority_risks": safe_get(risk, "high_priority_risks", 0),
                "red_flags": safe_get(risk, "red_flags", []),
                "top_risks": safe_get(risk, "top_risks", [])[:5],
                "scenarios": safe_get(risk, "scenarios", {}),
                "data_quality": safe_get(risk, "data_quality", "unknown"),
                "agent_status": safe_get(risk, "agent_status", "unknown"),
            },
            "sentiment": {
                "composite_score": safe_get(sentiment, "composite_score", 0),
                "composite_label": safe_get(sentiment, "composite_label", "NEUTRAL"),
                "confidence": safe_get(sentiment, "confidence", 0.5),
                "positive_themes": safe_get(sentiment, "positive_themes", []),
                "negative_themes": safe_get(sentiment, "negative_themes", []),
                "divergences": safe_get(sentiment, "divergences", []),
                "momentum": safe_get(sentiment, "momentum", "stable"),
                "peer_comparison": safe_get(sentiment, "peer_comparison", {}),
                "data_quality": safe_get(sentiment, "data_quality", "unknown"),
                "agent_status": safe_get(sentiment, "agent_status", "unknown"),
            },
        }
        return summary

    def _create_analysis_prompt(self, summary: Dict) -> str:
        """Create the synthesis prompt for the LLM."""
        # Extract data quality info
        fund_quality = summary['fundamental'].get('data_quality', 'unknown')
        fund_status = summary['fundamental'].get('agent_status', 'unknown')
        market_quality = summary['market'].get('data_quality', 'unknown')
        market_status = summary['market'].get('agent_status', 'unknown')
        risk_quality = summary['risk'].get('data_quality', 'unknown')
        risk_status = summary['risk'].get('agent_status', 'unknown')
        sentiment_quality = summary['sentiment'].get('data_quality', 'unknown')
        sentiment_status = summary['sentiment'].get('agent_status', 'unknown')
        
        prompt = f"""Synthesize the following agent analyses into a final investment decision.

DATA QUALITY ASSESSMENT:
- Fundamental: {fund_quality} (status: {fund_status})
- Market: {market_quality} (status: {market_status})
- Risk: {risk_quality} (status: {risk_status})
- Sentiment: {sentiment_quality} (status: {sentiment_status})

FUNDAMENTAL ANALYSIS (Weight: 25%):
- Score: {summary['fundamental']['overall_score']:.1f}/100
- Confidence: {summary['fundamental']['confidence']:.0%}
- Strengths: {summary['fundamental']['strengths']}
- Weaknesses: {summary['fundamental']['weaknesses']}
- Red Flags: {summary['fundamental']['red_flags']}
- Key Metrics: {summary['fundamental']['key_metrics']}

MARKET ANALYSIS (Weight: 20%):
- Score: {summary['market']['overall_score']:.1f}/100
- Confidence: {summary['market']['confidence']:.0%}
- Market Opportunity: {summary['market']['market_opportunity_summary']}
- Opportunities: {summary['market']['key_opportunities']}
- Risks: {summary['market']['key_risks']}
- TAM: {summary['market']['tam_analysis'].get('tam_usd', 'N/A')}
- Competitive Position: {summary['market']['competitive_analysis'].get('moat_strength', 'N/A')}

RISK ANALYSIS (Weight: 15%, inverted):
- Risk Score: {summary['risk']['overall_risk_score']:.1f}/100
- Confidence: {summary['risk']['confidence']:.0%}
- Risk Level: {summary['risk']['overall_risk_level']}
- High Priority Risks: {summary['risk']['high_priority_risks']}
- Red Flags: {summary['risk']['red_flags']}
- Top Risks: {summary['risk']['top_risks']}

SENTIMENT ANALYSIS (Weight: 10%):
- Composite Score: {summary['sentiment']['composite_score']:.2f}
- Label: {summary['sentiment']['composite_label']}
- Confidence: {summary['sentiment']['confidence']:.0%}
- Positive Themes: {summary['sentiment']['positive_themes']}
- Negative Themes: {summary['sentiment']['negative_themes']}
- Divergences: {summary['sentiment']['divergences']}
- Momentum: {summary['sentiment']['momentum']}

WEIGHTS: Fundamental 25%, Market 20%, Risk 15%, Sentiment 10%, Management 15%, Valuation 15%

SYNTHESIS REQUIRED:
1. Calculate weighted overall score (risk inverted)
2. Generate clear bull case with key drivers
3. Generate clear bear case with key risks
4. Map to recommendation (Aggressive Buy → Avoid)
5. Determine time horizon (Intraday → Very Long Term)
6. Assess risk level (Very Low → Extreme)
7. Provide position sizing guidance
8. Create entry strategy
9. Build monitoring plan
10. Generate probability-weighted scenarios
11. List positive/negative factors, risks, catalysts
12. Identify valuation/financial/market concerns
13. Document data limitations and confidence

MANDATORY: If a data source says "Insufficient Data" or "unknown", you MUST acknowledge this in your analysis. Do NOT generate generic analysis for missing data. Include data quality assessment in your final output."""
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
        for agent_name in ["fundamental", "market", "risk", "sentiment"]:
            data = summary.get(agent_name, {})
            if data.get("overall_score") is not None:
                evidence.append(f"{agent_name}: Score={data['overall_score']:.1f}, Conf={data.get('confidence', 0):.0%}")
        return evidence