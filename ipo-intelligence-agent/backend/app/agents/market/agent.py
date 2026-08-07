"""Market Analysis Agent - Analyzes market opportunity and competitive landscape."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus
from app.core.exceptions.base import AgentError


class MarketAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that analyzes market opportunity, TAM/SAM/SOM, and competitive positioning."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.MARKET,
            description="Analyzes market size, growth, competition, and positioning",
            version="1.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
    
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
- Key risks and opportunities"""
    
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
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute market analysis."""
        start_time = datetime.utcnow()
        
        try:
            company_profile = input_data.get("company_profile", {})
            industry_data = input_data.get("industry_data", {})
            competitor_data = input_data.get("competitors", [])
            financials = input_data.get("financials", [])
            
            # Extract key info
            sector = company_profile.get("sector", "")
            industry = company_profile.get("industry", "")
            business_model = company_profile.get("business_model", "")
            target_markets = company_profile.get("target_markets", [])
            key_products = company_profile.get("key_products", [])
            competitive_advantages = company_profile.get("competitive_advantages", [])
            
            # Perform analyses
            tam_analysis = self._estimate_tam(sector, industry, target_markets, industry_data)
            sam_analysis = self._estimate_sam(tam_analysis, company_profile, business_model)
            som_analysis = self._estimate_som(sam_analysis, company_profile, financials)
            competitive_analysis = self._analyze_competitive_landscape(
                competitor_data, company_profile
            )
            trends_analysis = self._analyze_market_trends(sector, industry, industry_data)
            positioning_analysis = self._evaluate_positioning(
                company_profile, competitive_analysis, competitive_advantages
            )
            
            # Calculate scores
            scores = {
                "tam_attractiveness": tam_analysis["score"],
                "sam_capture_potential": sam_analysis["score"],
                "som_realism": som_analysis["score"],
                "competitive_position": competitive_analysis["score"],
                "market_timing": trends_analysis["score"],
                "differentiation": positioning_analysis["score"],
            }
            
            overall_score = sum(scores.values()) / len(scores)
            confidence = self._calculate_confidence(
                industry_data, competitor_data, company_profile
            )
            
            result_data = {
                "overall_score": round(overall_score, 1),
                "confidence": confidence,
                "pillar_scores": scores,
                "tam_analysis": tam_analysis,
                "sam_analysis": sam_analysis,
                "som_analysis": som_analysis,
                "competitive_analysis": competitive_analysis,
                "trends_analysis": trends_analysis,
                "positioning_analysis": positioning_analysis,
                "market_opportunity_summary": self._generate_opportunity_summary(
                    tam_analysis, sam_analysis, som_analysis
                ),
                "key_risks": self._identify_market_risks(
                    competitive_analysis, trends_analysis, positioning_analysis
                ),
                "key_opportunities": self._identify_market_opportunities(
                    tam_analysis, trends_analysis, positioning_analysis
                ),
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                confidence=confidence,
                reasoning=self._generate_reasoning(result_data),
                evidence=self._collect_evidence(result_data),
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
    
    def _estimate_tam(
        self,
        sector: str,
        industry: str,
        target_markets: List[str],
        industry_data: Dict,
    ) -> Dict[str, Any]:
        """Estimate Total Addressable Market."""
        # In production, this would query market research databases
        # For now, use industry benchmarks
        
        tam_estimates = {
            "software": 500_000_000_000,
            "biotech": 200_000_000_000,
            "fintech": 300_000_000_000,
            "ai_ml": 150_000_000_000,
            "cybersecurity": 200_000_000_000,
            "semiconductors": 600_000_000_000,
            "renewable_energy": 1_000_000_000_000,
            "healthcare_services": 8_000_000_000_000,
            "ecommerce": 6_000_000_000_000,
        }
        
        tam = tam_estimates.get(industry.lower(), 100_000_000_000)
        
        # Adjust for target markets
        if "global" in [m.lower() for m in target_markets]:
            pass  # Already global
        elif len(target_markets) == 1:
            tam *= 0.3  # Single geography
        elif len(target_markets) <= 3:
            tam *= 0.6
        
        # Get growth rate
        cagr = industry_data.get("market_cagr", 0.15)
        
        score = 50
        if tam > 1_000_000_000_000:
            score += 25
        elif tam > 500_000_000_000:
            score += 15
        elif tam > 100_000_000_000:
            score += 10
        
        if cagr > 0.25:
            score += 15
        elif cagr > 0.15:
            score += 10
        elif cagr > 0.1:
            score += 5
        
        return {
            "tam_usd": tam,
            "tam_formatted": f"${tam/1e9:.1f}B",
            "cagr": cagr,
            "methodology": "Industry benchmarks adjusted for target markets",
            "key_drivers": industry_data.get("key_drivers", []),
            "score": min(100, max(0, score)),
        }
    
    def _estimate_sam(
        self,
        tam_analysis: Dict,
        company_profile: Dict,
        business_model: str,
    ) -> Dict[str, Any]:
        """Estimate Serviceable Addressable Market."""
        tam = tam_analysis["tam_usd"]
        
        # SAM is typically 10-30% of TAM for focused companies
        # Higher for platform/horizontal plays, lower for niche
        sam_pct = 0.15
        
        if "platform" in business_model.lower():
            sam_pct = 0.25
        elif "vertical" in business_model.lower() or "niche" in business_model.lower():
            sam_pct = 0.08
        elif "horizontal" in business_model.lower():
            sam_pct = 0.30
        
        sam = tam * sam_pct
        
        # Adjust for company stage
        stage = company_profile.get("stage", "growth")
        if stage == "early":
            sam *= 0.7
        elif stage == "mature":
            sam *= 1.2
        
        score = 50
        if sam > 10_000_000_000:
            score += 20
        elif sam > 1_000_000_000:
            score += 15
        elif sam > 100_000_000:
            score += 10
        
        # SAM/TAM ratio - too high might be unrealistic
        sam_tam_ratio = sam / tam
        if sam_tam_ratio > 0.5:
            score -= 10
        
        return {
            "sam_usd": sam,
            "sam_formatted": f"${sam/1e9:.1f}B",
            "sam_tam_ratio": sam_tam_ratio,
            "methodology": f"Applied {sam_pct:.0%} SAM/TAM ratio based on business model",
            "score": min(100, max(0, score)),
        }
    
    def _estimate_som(
        self,
        sam_analysis: Dict,
        company_profile: Dict,
        financials: List[Dict],
    ) -> Dict[str, Any]:
        """Estimate Serviceable Obtainable Market."""
        sam = sam_analysis["sam_usd"]
        
        # SOM typically 1-5% of SAM for realistic 3-5 year capture
        # Adjust based on current traction
        current_revenue = 0
        if financials:
            current_revenue = financials[0].get("revenue", 0)
        
        if current_revenue > 0:
            # Implied current market share
            current_share = current_revenue / sam
            # Project 3-5 year capture
            projected_share = min(current_share * 5, 0.05)  # Cap at 5%
        else:
            projected_share = 0.01  # 1% default
        
        som = sam * projected_share
        
        score = 50
        if projected_share > 0.03:
            score += 15
        elif projected_share > 0.01:
            score += 10
        elif projected_share > 0.005:
            score += 5
        
        # Check realism
        if som > 1_000_000_000 and current_revenue < 10_000_000:
            score -= 15  # Unrealistic jump
        
        return {
            "som_usd": som,
            "som_formatted": f"${som/1e6:.0f}M" if som < 1e9 else f"${som/1e9:.1f}B",
            "projected_market_share": projected_share,
            "current_revenue": current_revenue,
            "implied_growth": (som / current_revenue - 1) if current_revenue > 0 else None,
            "score": min(100, max(0, score)),
        }
    
    def _analyze_competitive_landscape(
        self,
        competitor_data: List[Dict],
        company_profile: Dict,
    ) -> Dict[str, Any]:
        """Analyze competitive positioning."""
        if not competitor_data:
            return {
                "score": 50,
                "details": "No competitor data available",
                "competitors": [],
                "market_structure": "unknown",
            }
        
        # Categorize competitors
        direct = [c for c in competitor_data if c.get("type") == "direct"]
        indirect = [c for c in competitor_data if c.get("type") == "indirect"]
        public = [c for c in competitor_data if c.get("public", False)]
        private = [c for c in competitor_data if not c.get("public", False)]
        
        # Market concentration
        total_competitors = len(competitor_data)
        public_count = len(public)
        
        # Competitive intensity
        intensity = "low"
        if total_competitors > 20:
            intensity = "very_high"
        elif total_competitors > 10:
            intensity = "high"
        elif total_competitors > 5:
            intensity = "moderate"
        
        # Assess moat
        advantages = company_profile.get("competitive_advantages", [])
        moat_strength = "weak"
        if len(advantages) >= 3:
            moat_strength = "strong"
        elif len(advantages) >= 1:
            moat_strength = "moderate"
        
        score = 50
        if intensity == "low":
            score += 15
        elif intensity == "moderate":
            score += 5
        elif intensity == "high":
            score -= 5
        else:
            score -= 15
        
        if moat_strength == "strong":
            score += 20
        elif moat_strength == "moderate":
            score += 10
        
        return {
            "score": min(100, max(0, score)),
            "total_competitors": total_competitors,
            "direct_competitors": len(direct),
            "indirect_competitors": len(indirect),
            "public_competitors": public_count,
            "private_competitors": len(private),
            "intensity": intensity,
            "moat_strength": moat_strength,
            "key_competitors": [
                {
                    "name": c.get("name"),
                    "public": c.get("public", False),
                    "estimated_revenue": c.get("revenue"),
                    "differentiation": c.get("differentiation"),
                }
                for c in competitor_data[:10]
            ],
            "market_structure": "fragmented" if total_competitors > 10 else "concentrated",
        }
    
    def _analyze_market_trends(
        self,
        sector: str,
        industry: str,
        industry_data: Dict,
    ) -> Dict[str, Any]:
        """Analyze market trends and timing."""
        tailwinds = industry_data.get("tailwinds", [])
        headwinds = industry_data.get("headwinds", [])
        cagr = industry_data.get("market_cagr", 0.15)
        lifecycle = industry_data.get("lifecycle", "growth")
        
        score = 50
        
        # Lifecycle
        if lifecycle == "emerging":
            score += 15
        elif lifecycle == "growth":
            score += 10
        elif lifecycle == "mature":
            score -= 5
        elif lifecycle == "declining":
            score -= 20
        
        # Tailwinds vs headwinds
        net_tailwinds = len(tailwinds) - len(headwinds)
        score += net_tailwinds * 5
        
        # CAGR
        if cagr > 0.25:
            score += 15
        elif cagr > 0.15:
            score += 10
        elif cagr > 0.1:
            score += 5
        elif cagr < 0:
            score -= 15
        
        return {
            "score": min(100, max(0, score)),
            "lifecycle": lifecycle,
            "cagr": cagr,
            "tailwinds": tailwinds,
            "headwinds": headwinds,
            "net_sentiment": "positive" if net_tailwinds > 0 else "negative",
            "timing_assessment": self._assess_timing(lifecycle, cagr, net_tailwinds),
        }
    
    def _assess_timing(self, lifecycle: str, cagr: float, net_tailwinds: int) -> str:
        """Assess market entry timing."""
        if lifecycle in ["emerging", "growth"] and cagr > 0.15 and net_tailwinds > 0:
            return "excellent"
        elif lifecycle == "growth" and cagr > 0.1:
            return "good"
        elif lifecycle == "mature" and cagr > 0.05:
            return "fair"
        else:
            return "challenging"
    
    def _evaluate_positioning(
        self,
        company_profile: Dict,
        competitive_analysis: Dict,
        advantages: List[str],
    ) -> Dict[str, Any]:
        """Evaluate competitive positioning."""
        differentiation = company_profile.get("differentiation", "")
        value_prop = company_profile.get("value_proposition", "")
        switching_costs = company_profile.get("switching_costs", "medium")
        network_effects = company_profile.get("network_effects", False)
        brand_strength = company_profile.get("brand_strength", "building")
        
        score = 50
        
        # Differentiation clarity
        if differentiation and len(differentiation) > 100:
            score += 10
        elif differentiation:
            score += 5
        
        # Switching costs
        if switching_costs == "high":
            score += 15
        elif switching_costs == "medium":
            score += 5
        elif switching_costs == "low":
            score -= 5
        
        # Network effects
        if network_effects:
            score += 15
        
        # Brand
        if brand_strength == "strong":
            score += 10
        elif brand_strength == "established":
            score += 5
        
        # Competitive advantages count
        score += min(15, len(advantages) * 3)
        
        return {
            "score": min(100, max(0, score)),
            "differentiation": differentiation,
            "value_proposition": value_prop,
            "switching_costs": switching_costs,
            "network_effects": network_effects,
            "brand_strength": brand_strength,
            "advantages": advantages,
            "positioning_statement": self._generate_positioning_statement(
                company_profile, competitive_analysis
            ),
        }
    
    def _generate_positioning_statement(
        self,
        company_profile: Dict,
        competitive_analysis: Dict,
    ) -> str:
        """Generate positioning statement."""
        name = company_profile.get("common_name", "The Company")
        industry = company_profile.get("industry", "its market")
        differentiation = company_profile.get("differentiation", "unique approach")
        
        return (
            f"{name} is positioned as a {differentiation} player in {industry}. "
            f"With {competitive_analysis.get('direct_competitors', 0)} direct competitors "
            f"and a {competitive_analysis.get('moat_strength', 'moderate')} moat, "
            f"the company targets {company_profile.get('target_customer', 'enterprise customers')}."
        )
    
    def _generate_opportunity_summary(
        self,
        tam: Dict,
        sam: Dict,
        som: Dict,
    ) -> str:
        """Generate market opportunity summary."""
        return (
            f"Market Opportunity: TAM of {tam['tam_formatted']} "
            f"({tam['cagr']:.0%} CAGR), SAM of {sam['sam_formatted']}, "
            f"with realistic SOM of {som['som_formatted']} "
            f"({som['projected_market_share']:.1%} market share)."
        )
    
    def _identify_market_risks(
        self,
        competitive: Dict,
        trends: Dict,
        positioning: Dict,
    ) -> List[str]:
        """Identify market risks."""
        risks = []
        
        if competitive.get("intensity") in ["high", "very_high"]:
            risks.append("High competitive intensity may pressure margins")
        
        if competitive.get("moat_strength") == "weak":
            risks.append("Weak competitive moat vulnerable to disruption")
        
        if trends.get("lifecycle") == "mature":
            risks.append("Market maturity limits growth potential")
        
        if trends.get("headwinds"):
            risks.append(f"Headwinds: {', '.join(trends['headwinds'][:3])}")
        
        if positioning.get("switching_costs") == "low":
            risks.append("Low switching costs enable customer churn")
        
        return risks
    
    def _identify_market_opportunities(
        self,
        tam: Dict,
        trends: Dict,
        positioning: Dict,
    ) -> List[str]:
        """Identify market opportunities."""
        opps = []
        
        if tam.get("tam_usd", 0) > 1e12:
            opps.append("Massive TAM with room for multiple winners")
        
        if trends.get("tailwinds"):
            opps.append(f"Strong tailwinds: {', '.join(trends['tailwinds'][:3])}")
        
        if positioning.get("network_effects"):
            opps.append("Network effects create winner-take-most dynamics")
        
        if positioning.get("switching_costs") == "high":
            opps.append("High switching costs drive retention and expansion")
        
        return opps
    
    def _calculate_confidence(
        self,
        industry_data: Dict,
        competitor_data: List,
        company_profile: Dict,
    ) -> float:
        """Calculate confidence in analysis."""
        confidence = 0.4
        
        if industry_data.get("market_cagr") is not None:
            confidence += 0.15
        if industry_data.get("tailwinds"):
            confidence += 0.1
        if len(competitor_data) >= 5:
            confidence += 0.15
        elif len(competitor_data) > 0:
            confidence += 0.1
        if company_profile.get("competitive_advantages"):
            confidence += 0.1
        if company_profile.get("tam"):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _generate_reasoning(self, result: Dict) -> str:
        """Generate reasoning summary."""
        parts = [
            f"Market Analysis Score: {result['overall_score']:.1f}/100",
            f"Confidence: {result['confidence']:.0%}",
            "",
            "Pillar Scores:",
        ]
        
        for pillar, score in result["pillar_scores"].items():
            parts.append(f"  - {pillar.replace('_', ' ').title()}: {score:.1f}")
        
        parts.append(f"\n{result['market_opportunity_summary']}")
        
        if result["key_opportunities"]:
            parts.append("\nOpportunities:")
            for o in result["key_opportunities"]:
                parts.append(f"  + {o}")
        
        if result["key_risks"]:
            parts.append("\nRisks:")
            for r in result["key_risks"]:
                parts.append(f"  - {r}")
        
        return "\n".join(parts)
    
    def _collect_evidence(self, result: Dict) -> List[str]:
        """Collect evidence citations."""
        evidence = []
        
        tam = result.get("tam_analysis", {})
        if tam.get("tam_usd"):
            evidence.append(f"TAM: {tam['tam_formatted']} ({tam['cagr']:.0%} CAGR)")
        
        sam = result.get("sam_analysis", {})
        if sam.get("sam_usd"):
            evidence.append(f"SAM: {sam['sam_formatted']} ({sam['sam_tam_ratio']:.0%} of TAM)")
        
        som = result.get("som_analysis", {})
        if som.get("som_usd"):
            evidence.append(f"SOM: {som['som_formatted']} ({som['projected_market_share']:.1%} share)")
        
        comp = result.get("competitive_analysis", {})
        if comp.get("total_competitors"):
            evidence.append(f"Competitors: {comp['total_competitors']} total ({comp['direct_competitors']} direct)")
        
        trends = result.get("trends_analysis", {})
        if trends.get("lifecycle"):
            evidence.append(f"Market lifecycle: {trends['lifecycle']} ({trends['cagr']:.0%} CAGR)")
        
        return evidence