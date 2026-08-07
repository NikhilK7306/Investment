"""Decision Support Agent - Synthesizes all analyses into final recommendation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, InvestmentStrategy, RiskLevel, TimeHorizon
from app.domain.entities.entities import OverallAnalysis
from app.domain.value_objects.value_objects import InvestmentThesis
from app.core.exceptions.base import AgentError


class DecisionSupportAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that synthesizes all analyses into final investment decision."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.DECISION,
            description="Synthesizes all agent analyses into final investment recommendation",
            version="1.0.0",
            max_retries=1,
            timeout_seconds=120,
        )
        
        # Default scoring weights
        self.weights = {
            "fundamental": 0.25,
            "market": 0.20,
            "risk": 0.15,  # Inverted
            "sentiment": 0.10,
            "management": 0.15,  # Would come from fundamental
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
- Confidence and uncertainty quantification"""
    
    @property
    def available_tools(self) -> List[str]:
        return [
            "calculate_weighted_score",
            "generate_bull_bear_cases",
            "determine_recommendation",
            "calculate_position_size",
            "create_monitoring_plan",
        ]
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute decision synthesis."""
        start_time = datetime.utcnow()
        
        try:
            # Extract all agent results
            fundamental = input_data.get("fundamental_analysis", {})
            market = input_data.get("market_analysis", {})
            risk = input_data.get("risk_analysis", {})
            sentiment = input_data.get("sentiment_analysis", {})
            
            # Get scores
            fundamental_score = fundamental.get("overall_score", 50)
            market_score = market.get("overall_score", 50)
            risk_score = 100 - risk.get("overall_risk_score", 50)  # Invert
            sentiment_score = self._sentiment_to_score(sentiment.get("composite_score", 0))
            
            # Calculate weighted score
            scores = {
                "fundamental": fundamental_score,
                "market": market_score,
                "risk": risk_score,
                "sentiment": sentiment_score,
            }
            
            weighted_score = sum(
                scores[k] * self.weights.get(k, 0)
                for k in scores
            )
            
            # Confidence-weighted
            confidence = self._calculate_confidence(
                fundamental, market, risk, sentiment
            )
            
            final_score = round(weighted_score * confidence + 50 * (1 - confidence), 1)
            
            # Determine recommendation
            recommendation = self._score_to_recommendation(final_score)
            time_horizon = self._determine_time_horizon(fundamental, market, risk)
            risk_level = self._score_to_risk_level(risk.get("overall_risk_score", 50))
            
            # Generate thesis
            bull_case = self._generate_bull_case(fundamental, market, sentiment)
            bear_case = self._generate_bear_case(fundamental, market, risk)
            key_risks = self._extract_key_risks(risk, fundamental, market)
            key_catalysts = self._extract_key_catalysts(fundamental, market)
            
            # Position sizing
            position_guidance = self._calculate_position_guidance(
                final_score, confidence, risk_level, time_horizon
            )
            
            # Monitoring plan
            monitoring = self._create_monitoring_plan(
                fundamental, market, risk, sentiment
            )
            
            # Entry strategy
            entry_strategy = self._generate_entry_strategy(
                recommendation, risk_level, time_horizon
            )
            
            result_data = {
                "overall_score": final_score,
                "confidence": confidence,
                "recommendation": recommendation.value,
                "risk_level": risk_level.value,
                "time_horizon": time_horizon.value,
                "pillar_scores": scores,
                "weights_used": self.weights,
                "investment_thesis": {
                    "bull_case": bull_case,
                    "bear_case": bear_case,
                    "key_risks": key_risks,
                    "key_catalysts": key_catalysts,
                    "assumptions": self._list_key_assumptions(input_data),
                },
                "position_guidance": position_guidance,
                "entry_strategy": entry_strategy,
                "monitoring_plan": monitoring,
                "scenario_analysis": self._generate_scenarios(
                    final_score, fundamental, market, risk
                ),
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                confidence=confidence,
                reasoning=self._generate_reasoning(result_data),
                evidence=self._collect_evidence(input_data),
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
    
    def _sentiment_to_score(self, sentiment_score: float) -> float:
        """Convert -1 to 1 sentiment to 0-100 score."""
        return (sentiment_score + 1) * 50
    
    def _calculate_confidence(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
    ) -> float:
        """Calculate overall confidence."""
        confidences = [
            fundamental.get("confidence", 0.5),
            market.get("confidence", 0.5),
            risk.get("confidence", 0.5),
            sentiment.get("confidence", 0.5),
        ]
        
        # Weight by importance
        weights = [0.35, 0.25, 0.25, 0.15]
        weighted_conf = sum(c * w for c, w in zip(confidences, weights))
        
        # Penalize if any critical data missing
        if fundamental.get("overall_score", 0) == 0:
            weighted_conf *= 0.7
        
        return round(min(1.0, max(0.1, weighted_conf)), 2)
    
    def _score_to_recommendation(self, score: float) -> InvestmentStrategy:
        """Map score to recommendation."""
        if score >= 90:
            return InvestmentStrategy.AGGRESSIVE_BUY
        elif score >= 70:
            return InvestmentStrategy.BUY
        elif score >= 55:
            return InvestmentStrategy.ACCUMULATE
        elif score >= 45:
            return InvestmentStrategy.HOLD
        elif score >= 35:
            return InvestmentStrategy.WATCH
        elif score >= 25:
            return InvestmentStrategy.REDUCE
        elif score >= 15:
            return InvestmentStrategy.SELL
        else:
            return InvestmentStrategy.AVOID
    
    def _determine_time_horizon(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
    ) -> TimeHorizon:
        """Determine appropriate time horizon."""
        # High growth + strong fundamentals = longer horizon
        growth = fundamental.get("growth_analysis", {}).get("score", 50)
        market_timing = market.get("trends_analysis", {}).get("timing_assessment", "fair")
        risk_level = risk.get("overall_risk_score", 50)
        
        if growth > 70 and market_timing in ["excellent", "good"] and risk_level < 50:
            return TimeHorizon.LONG_TERM
        elif growth > 50 and risk_level < 60:
            return TimeHorizon.MEDIUM_TERM
        elif risk_level < 40:
            return TimeHorizon.MEDIUM_TERM
        else:
            return TimeHorizon.SHORT_TERM
    
    def _score_to_risk_level(self, risk_score: float) -> RiskLevel:
        """Map risk score to level."""
        if risk_score <= 20:
            return RiskLevel.VERY_LOW
        elif risk_score <= 35:
            return RiskLevel.LOW
        elif risk_score <= 50:
            return RiskLevel.MODERATE
        elif risk_score <= 65:
            return RiskLevel.HIGH
        elif risk_score <= 80:
            return RiskLevel.VERY_HIGH
        else:
            return RiskLevel.EXTREME
    
    def _generate_bull_case(
        self,
        fundamental: Dict,
        market: Dict,
        sentiment: Dict,
    ) -> str:
        """Generate bull case narrative."""
        parts = []
        
        # Fundamental strengths
        f_strengths = fundamental.get("strengths", [])
        if f_strengths:
            parts.append("FUNDAMENTAL STRENGTHS:")
            for s in f_strengths[:3]:
                parts.append(f"  • {s}")
        
        # Market opportunity
        m_opp = market.get("market_opportunity_summary", "")
        if m_opp:
            parts.append(f"\nMARKET OPPORTUNITY:\n  {m_opp}")
        
        # Competitive position
        comp = market.get("positioning_analysis", {})
        if comp.get("moat_strength") in ["strong", "moderate"]:
            parts.append(f"\nCOMPETITIVE POSITION: {comp.get('moat_strength', '').title()} moat with {comp.get('switching_costs', 'moderate')} switching costs")
        
        # Positive catalysts
        catalysts = market.get("key_opportunities", [])
        if catalysts:
            parts.append("\nPOSITIVE CATALYSTS:")
            for c in catalysts[:3]:
                parts.append(f"  • {c}")
        
        # Sentiment
        if sentiment.get("composite_score", 0) > 0.2:
            parts.append(f"\nSENTIMENT: Positive ({sentiment.get('composite_label', 'neutral')})")
        
        return "\n".join(parts) if parts else "Bull case under development"
    
    def _generate_bear_case(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
    ) -> str:
        """Generate bear case narrative."""
        parts = []
        
        # Fundamental weaknesses
        f_weaknesses = fundamental.get("weaknesses", [])
        if f_weaknesses:
            parts.append("FUNDAMENTAL WEAKNESSES:")
            for w in f_weaknesses[:3]:
                parts.append(f"  • {w}")
        
        # Red flags
        red_flags = fundamental.get("red_flags", [])
        if red_flags:
            parts.append("\n🚩 RED FLAGS:")
            for r in red_flags[:3]:
                parts.append(f"  • {r}")
        
        # Risk factors
        risk_factors = risk.get("red_flags", [])
        if risk_factors:
            parts.append("\nKEY RISKS:")
            for r in risk_factors[:3]:
                parts.append(f"  • {r}")
        
        # Market risks
        m_risks = market.get("key_risks", [])
        if m_risks:
            parts.append("\nMARKET RISKS:")
            for r in m_risks[:3]:
                parts.append(f"  • {r}")
        
        # Competitive threats
        comp = market.get("competitive_analysis", {})
        if comp.get("intensity") in ["high", "very_high"]:
            parts.append(f"\nCOMPETITION: {comp.get('intensity', '').title()} intensity with {comp.get('total_competitors', 0)} competitors")
        
        return "\n".join(parts) if parts else "Bear case under development"
    
    def _extract_key_risks(
        self,
        risk: Dict,
        fundamental: Dict,
        market: Dict,
    ) -> List[str]:
        """Extract top 5 key risks."""
        risks = []
        
        # From risk analysis
        risk_factors = risk.get("red_flags", [])
        risks.extend(risk_factors[:3])
        
        # From fundamental red flags
        f_flags = fundamental.get("red_flags", [])
        risks.extend(f_flags[:2])
        
        # From market risks
        m_risks = market.get("key_risks", [])
        risks.extend(m_risks[:2])
        
        # Deduplicate and limit
        seen = set()
        unique = []
        for r in risks:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        
        return unique[:5]
    
    def _extract_key_catalysts(
        self,
        fundamental: Dict,
        market: Dict,
    ) -> List[str]:
        """Extract key catalysts."""
        catalysts = []
        
        # From market opportunities
        opps = market.get("key_opportunities", [])
        catalysts.extend(opps[:3])
        
        # From fundamental strengths
        strengths = fundamental.get("strengths", [])
        catalysts.extend([f"Execution on: {s}" for s in strengths[:2]])
        
        # Product launches, expansions (would come from company data)
        catalysts.extend([
            "New product launches",
            "Geographic expansion",
            "Strategic partnerships",
            "Margin improvement initiatives",
        ])
        
        seen = set()
        unique = []
        for c in catalysts:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        
        return unique[:5]
    
    def _list_key_assumptions(self, input_data: Dict) -> List[str]:
        """List key assumptions underlying the thesis."""
        return [
            "Financial projections based on company guidance and analyst estimates",
            "Market growth rates based on third-party research",
            "No major regulatory changes in core markets",
            "Management executes on stated strategy",
            "Macro environment remains supportive",
            "Competitive landscape evolves as expected",
            "IPO proceeds deployed as disclosed",
        ]
    
    def _calculate_position_guidance(
        self,
        score: float,
        confidence: float,
        risk_level: RiskLevel,
        time_horizon: TimeHorizon,
    ) -> Dict[str, Any]:
        """Calculate position sizing guidance."""
        # Base sizing from score and confidence
        base_size = (score / 100) * confidence * 10  # 0-10% of portfolio
        
        # Risk adjustment
        risk_mult = {
            RiskLevel.VERY_LOW: 1.5,
            RiskLevel.LOW: 1.2,
            RiskLevel.MODERATE: 1.0,
            RiskLevel.HIGH: 0.7,
            RiskLevel.VERY_HIGH: 0.4,
            RiskLevel.EXTREME: 0.2,
        }.get(risk_level, 1.0)
        
        # Time horizon adjustment
        horizon_mult = {
            TimeHorizon.VERY_LONG_TERM: 1.2,
            TimeHorizon.LONG_TERM: 1.1,
            TimeHorizon.MEDIUM_TERM: 1.0,
            TimeHorizon.SHORT_TERM: 0.8,
            TimeHorizon.INTRADAY: 0.3,
        }.get(time_horizon, 1.0)
        
        suggested_max = round(base_size * risk_mult * horizon_mult, 1)
        suggested_max = min(10, max(0.5, suggested_max))  # Cap at 10%, floor at 0.5%
        
        return {
            "suggested_max_pct": suggested_max,
            "suggested_entry_pct": round(suggested_max * 0.5, 1),  # Start with half
            "scaling_plan": [
                f"Initial: {round(suggested_max * 0.5, 1)}%",
                f"On confirmation: +{round(suggested_max * 0.3, 1)}%",
                f"Full position: {suggested_max}%",
            ],
            "risk_adjusted": True,
            "notes": f"Adjusted for {risk_level.value} risk and {time_horizon.value} horizon",
        }
    
    def _generate_entry_strategy(
        self,
        recommendation: InvestmentStrategy,
        risk_level: RiskLevel,
        time_horizon: TimeHorizon,
    ) -> Dict[str, Any]:
        """Generate entry strategy."""
        if recommendation in [InvestmentStrategy.AGGRESSIVE_BUY, InvestmentStrategy.BUY]:
            strategy = "staged"
            stages = 3
        elif recommendation == InvestmentStrategy.ACCUMULATE:
            strategy = "staged"
            stages = 4
        else:
            strategy = "wait_for_catalyst"
            stages = 0
        
        return {
            "strategy": strategy,
            "stages": stages,
            "trigger_conditions": [
                "Post-lockup stabilization",
                "First earnings as public company",
                "Analyst initiation coverage",
                "Technical support level",
            ],
            "price_targets": {
                "conservative": "Analyst median target",
                "base": "DCF fair value",
                "bullish": "Sum-of-parts + premium",
            },
            "stop_loss": f"{15 + risk_level.value * 5}% below entry" if strategy != "wait_for_catalyst" else "N/A",
        }
    
    def _create_monitoring_plan(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
    ) -> Dict[str, Any]:
        """Create monitoring checklist."""
        return {
            "weekly": [
                "News flow and sentiment changes",
                "Analyst rating changes",
                "Insider trading filings (Form 4)",
                "Short interest changes",
            ],
            "monthly": [
                "Revenue growth vs guidance",
                "Margin trends",
                "Cash burn / FCF trajectory",
                "Competitive announcements",
                "Market share data",
            ],
            "quarterly": [
                "Earnings calls and transcripts",
                "Updated financial models",
                "Guidance vs actuals",
                "Capital allocation decisions",
                "Management changes",
            ],
            "key_metrics_to_watch": [
                "Revenue YoY growth",
                "Gross margin trend",
                "FCF margin",
                "Customer acquisition cost",
                "Net revenue retention",
                "Rule of 40 score",
            ],
            "red_line_alerts": [
                "Revenue miss >10%",
                "Guidance reduction",
                "CFO/CEO departure",
                "SEC investigation",
                "Major customer loss",
                "Debt covenant breach risk",
            ],
        }
    
    def _generate_scenarios(
        self,
        score: float,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
    ) -> Dict[str, Any]:
        """Generate probability-weighted scenarios."""
        base_return = (score - 50) / 10  # -5% to +5% base
        
        return {
            "bull": {
                "probability": 0.25,
                "return": base_return + 20,
                "drivers": [
                    "Above-consensus execution",
                    "Market share gains",
                    "Multiple expansion",
                    "Positive M&A",
                ],
            },
            "base": {
                "probability": 0.50,
                "return": base_return,
                "drivers": [
                    "Meets guidance",
                    "Stable margins",
                    "Market grows at trend",
                ],
            },
            "bear": {
                "probability": 0.25,
                "return": base_return - 25,
                "drivers": [
                    "Guidance miss",
                    "Margin compression",
                    "Competitive loss",
                    "Macro headwinds",
                ],
            },
            "expected_value": round(
                0.25 * (base_return + 20) +
                0.50 * base_return +
                0.25 * (base_return - 25),
                1,
            ),
        }
    
    def _generate_reasoning(self, result: Dict) -> str:
        """Generate reasoning."""
        parts = [
            f"FINAL RECOMMENDATION: {result['recommendation'].replace('_', ' ').title()}",
            f"Overall Score: {result['overall_score']:.1f}/100",
            f"Confidence: {result['confidence']:.0%}",
            f"Risk Level: {result['risk_level']}",
            f"Time Horizon: {result['time_horizon']}",
            "",
            "PILLAR SCORES:",
        ]
        
        for pillar, score in result["pillar_scores"].items():
            parts.append(f"  {pillar.title()}: {score:.1f} (weight: {result['weights_used'].get(pillar, 0):.0%})")
        
        parts.append(f"\nEXPECTED VALUE: {result['scenario_analysis']['expected_value']:.1f}%")
        
        if result["investment_thesis"]["bull_case"]:
            parts.append(f"\nBULL CASE:\n{result['investment_thesis']['bull_case'][:300]}...")
        
        if result["investment_thesis"]["bear_case"]:
            parts.append(f"\nBEAR CASE:\n{result['investment_thesis']['bear_case'][:300]}...")
        
        return "\n".join(parts)
    
    def _collect_evidence(self, input_data: Dict) -> List[str]:
        """Collect evidence from all analyses."""
        evidence = []
        
        for agent_name in ["fundamental_analysis", "market_analysis", "risk_analysis", "sentiment_analysis"]:
            data = input_data.get(agent_name, {})
            if data.get("overall_score") is not None:
                evidence.append(f"{agent_name}: Score={data['overall_score']:.1f}, Conf={data.get('confidence', 0):.0%}")
        
        return evidence