"""Fundamental Analysis Agent - Analyzes company financial health."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus
from app.domain.value_objects.value_objects import FinancialMetrics, ScoreComponent
from app.domain.value_objects.value_objects import Money, Percentage, Ratio
from app.core.exceptions.base import AgentError


class FundamentalAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that performs fundamental financial analysis."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.FUNDAMENTAL,
            description="Analyzes company financial health, profitability, and growth",
            version="1.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
    
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

Be rigorous, quantitative, and cite specific numbers. Highlight both positives and negatives."""
    
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
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute fundamental analysis."""
        start_time = datetime.utcnow()
        
        try:
            # Extract input data
            financials = input_data.get("financials", [])
            company_profile = input_data.get("company_profile", {})
            public_comps = input_data.get("public_comps", [])
            
            if not financials:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.FAILED,
                    error="No financial data provided",
                    error_type="MISSING_DATA",
                )
            
            # Parse financial metrics
            latest = financials[0] if financials else {}
            metrics = self._parse_financial_metrics(latest)
            
            # Perform analysis pillars
            revenue_analysis = self._analyze_revenue(financials, metrics)
            profitability_analysis = self._analyze_profitability(metrics)
            balance_sheet_analysis = self._analyze_balance_sheet(metrics)
            cash_flow_analysis = self._analyze_cash_flow(metrics)
            valuation_analysis = self._analyze_valuation(metrics, public_comps)
            growth_analysis = self._analyze_growth_sustainability(
                financials, company_profile, metrics
            )
            
            # Calculate scores
            scores = self._calculate_scores(
                revenue_analysis,
                profitability_analysis,
                balance_sheet_analysis,
                cash_flow_analysis,
                valuation_analysis,
                growth_analysis,
            )
            
            overall_score = sum(scores.values()) / len(scores)
            confidence = self._calculate_confidence(financials, metrics)
            
            # Build result
            result_data = {
                "overall_score": round(overall_score, 1),
                "confidence": confidence,
                "pillar_scores": scores,
                "revenue_analysis": revenue_analysis,
                "profitability_analysis": profitability_analysis,
                "balance_sheet_analysis": balance_sheet_analysis,
                "cash_flow_analysis": cash_flow_analysis,
                "valuation_analysis": valuation_analysis,
                "growth_analysis": growth_analysis,
                "key_metrics": self._extract_key_metrics(metrics),
                "strengths": self._identify_strengths(
                    revenue_analysis, profitability_analysis,
                    balance_sheet_analysis, cash_flow_analysis, growth_analysis
                ),
                "weaknesses": self._identify_weaknesses(
                    revenue_analysis, profitability_analysis,
                    balance_sheet_analysis, cash_flow_analysis, growth_analysis
                ),
                "red_flags": self._identify_red_flags(metrics, financials),
                "public_comps": public_comps[:5] if public_comps else [],
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                confidence=confidence,
                reasoning=self._generate_reasoning(result_data),
                evidence=self._collect_evidence(metrics, financials),
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
    
    def _parse_financial_metrics(self, data: Dict[str, Any]) -> FinancialMetrics:
        """Parse raw financial data into metrics object."""
        def money(val, curr="USD"):
            if val is None:
                return None
            return Money(val, curr)
        
        def pct(val):
            if val is None:
                return None
            return Percentage.from_decimal(val)
        
        def ratio(val, name, desc=""):
            if val is None:
                return None
            return Ratio(val, name, desc)
        
        return FinancialMetrics(
            revenue=money(data.get("revenue")),
            revenue_growth_yoy=pct(data.get("revenue_growth_yoy")),
            revenue_growth_qoq=pct(data.get("revenue_growth_qoq")),
            gross_profit=money(data.get("gross_profit")),
            gross_margin=pct(data.get("gross_margin")),
            operating_income=money(data.get("operating_income")),
            operating_margin=pct(data.get("operating_margin")),
            net_income=money(data.get("net_income")),
            net_margin=pct(data.get("net_margin")),
            ebitda=money(data.get("ebitda")),
            ebitda_margin=pct(data.get("ebitda_margin")),
            free_cash_flow=money(data.get("free_cash_flow")),
            fcf_margin=pct(data.get("fcf_margin")),
            total_assets=money(data.get("total_assets")),
            total_liabilities=money(data.get("total_liabilities")),
            total_equity=money(data.get("total_equity")),
            cash_and_equivalents=money(data.get("cash_and_equivalents")),
            total_debt=money(data.get("total_debt")),
            debt_to_equity=ratio(data.get("debt_to_equity"), "Debt/Equity"),
            current_ratio=ratio(data.get("current_ratio"), "Current Ratio"),
            quick_ratio=ratio(data.get("quick_ratio"), "Quick Ratio"),
            roe=pct(data.get("roe")),
            roa=pct(data.get("roa")),
            roic=pct(data.get("roic")),
            pe_ratio=ratio(data.get("pe_ratio"), "P/E"),
            ps_ratio=ratio(data.get("ps_ratio"), "P/S"),
            ev_ebitda=ratio(data.get("ev_ebitda"), "EV/EBITDA"),
            ev_revenue=ratio(data.get("ev_revenue"), "EV/Revenue"),
            revenue_cagr_3y=pct(data.get("revenue_cagr_3y")),
            revenue_cagr_5y=pct(data.get("revenue_cagr_5y")),
            fcf_conversion=pct(data.get("fcf_conversion")),
        )
    
    def _analyze_revenue(
        self,
        financials: List[Dict],
        metrics: FinancialMetrics,
    ) -> Dict[str, Any]:
        """Analyze revenue quality and growth."""
        analysis = {
            "score": 0,
            "details": [],
            "metrics": {},
        }
        
        score = 50  # Base
        
        # Growth
        if metrics.revenue_growth_yoy:
            growth = metrics.revenue_growth_yoy.to_decimal()
            analysis["metrics"]["yoy_growth"] = growth
            if growth > 0.5:
                score += 20
                analysis["details"].append(f"Exceptional YoY growth: {growth:.1%}")
            elif growth > 0.3:
                score += 15
                analysis["details"].append(f"Strong YoY growth: {growth:.1%}")
            elif growth > 0.15:
                score += 10
                analysis["details"].append(f"Healthy YoY growth: {growth:.1%}")
            elif growth > 0:
                score += 5
            else:
                score -= 10
                analysis["details"].append(f"Declining revenue: {growth:.1%}")
        
        # CAGR
        if metrics.revenue_cagr_3y:
            cagr = metrics.revenue_cagr_3y.to_decimal()
            analysis["metrics"]["cagr_3y"] = cagr
            if cagr > 0.4:
                score += 10
            elif cagr > 0.25:
                score += 5
        
        # Gross margin
        if metrics.gross_margin:
            gm = metrics.gross_margin.to_decimal()
            analysis["metrics"]["gross_margin"] = gm
            if gm > 0.75:
                score += 10
                analysis["details"].append(f"Excellent gross margin: {gm:.1%}")
            elif gm > 0.5:
                score += 5
            elif gm < 0.3:
                score -= 10
                analysis["details"].append(f"Low gross margin: {gm:.1%}")
        
        # Revenue concentration (would need segment data)
        analysis["details"].append("Revenue concentration analysis requires segment data")
        
        analysis["score"] = max(0, min(100, score))
        return analysis
    
    def _analyze_profitability(self, metrics: FinancialMetrics) -> Dict[str, Any]:
        """Analyze profitability metrics."""
        analysis = {"score": 0, "details": [], "metrics": {}}
        score = 50
        
        # Operating margin
        if metrics.operating_margin:
            om = metrics.operating_margin.to_decimal()
            analysis["metrics"]["operating_margin"] = om
            if om > 0.2:
                score += 20
                analysis["details"].append(f"Strong operating margin: {om:.1%}")
            elif om > 0.1:
                score += 10
            elif om > 0:
                score += 5
            else:
                score -= 10
                analysis["details"].append(f"Negative operating margin: {om:.1%}")
        
        # Net margin
        if metrics.net_margin:
            nm = metrics.net_margin.to_decimal()
            analysis["metrics"]["net_margin"] = nm
        
        # EBITDA margin
        if metrics.ebitda_margin:
            ebitda_m = metrics.ebitda_margin.to_decimal()
            analysis["metrics"]["ebitda_margin"] = ebitda_m
            if ebitda_m > 0.3:
                score += 10
        
        # ROE/ROIC
        if metrics.roe:
            roe = metrics.roe.to_decimal()
            analysis["metrics"]["roe"] = roe
            if roe > 0.2:
                score += 10
        
        if metrics.roic:
            roic = metrics.roic.to_decimal()
            analysis["metrics"]["roic"] = roic
            if roic > 0.15:
                score += 10
        
        analysis["score"] = max(0, min(100, score))
        return analysis
    
    def _analyze_balance_sheet(self, metrics: FinancialMetrics) -> Dict[str, Any]:
        """Analyze balance sheet strength."""
        analysis = {"score": 0, "details": [], "metrics": {}}
        score = 50
        
        # Cash position
        if metrics.cash_and_equivalents:
            cash = metrics.cash_and_equivalents.amount
            analysis["metrics"]["cash"] = float(cash)
            if cash > 100_000_000:
                score += 15
            elif cash > 50_000_000:
                score += 10
            elif cash > 10_000_000:
                score += 5
        
        # Debt levels
        if metrics.total_debt and metrics.total_equity:
            debt = metrics.total_debt.amount
            equity = metrics.total_equity.amount
            if equity > 0:
                d_e = debt / equity
                analysis["metrics"]["debt_to_equity"] = d_e
                if d_e < 0.3:
                    score += 15
                elif d_e < 0.5:
                    score += 10
                elif d_e < 1:
                    score += 5
                elif d_e > 2:
                    score -= 15
                    analysis["details"].append(f"High leverage: D/E = {d_e:.2f}")
        
        # Current ratio
        if metrics.current_ratio:
            cr = metrics.current_ratio.value
            analysis["metrics"]["current_ratio"] = cr
            if cr > 2:
                score += 10
            elif cr > 1.5:
                score += 5
            elif cr < 1:
                score -= 10
        
        # Interest coverage
        if metrics.ebitda and metrics.total_debt:
            # Simplified - would need interest expense
            pass
        
        analysis["score"] = max(0, min(100, score))
        return analysis
    
    def _analyze_cash_flow(self, metrics: FinancialMetrics) -> Dict[str, Any]:
        """Analyze cash flow quality."""
        analysis = {"score": 0, "details": [], "metrics": {}}
        score = 50
        
        # Operating cash flow
        if metrics.operating_cash_flow:
            ocf = metrics.operating_cash_flow.amount
            analysis["metrics"]["operating_cash_flow"] = float(ocf)
            if ocf > 0:
                score += 15
            else:
                score -= 20
        
        # Free cash flow
        if metrics.free_cash_flow:
            fcf = metrics.free_cash_flow.amount
            analysis["metrics"]["free_cash_flow"] = float(fcf)
            if fcf > 0:
                score += 20
                analysis["details"].append(f"Positive FCF: ${fcf:,.0f}")
            else:
                score -= 10
        
        # FCF margin
        if metrics.fcf_margin:
            fcf_m = metrics.fcf_margin.to_decimal()
            analysis["metrics"]["fcf_margin"] = fcf_m
            if fcf_m > 0.2:
                score += 10
            elif fcf_m > 0.1:
                score += 5
        
        # FCF conversion
        if metrics.fcf_conversion:
            fcf_conv = metrics.fcf_conversion.to_decimal()
            analysis["metrics"]["fcf_conversion"] = fcf_conv
            if fcf_conv > 1:
                score += 10
        
        analysis["score"] = max(0, min(100, score))
        return analysis
    
    def _analyze_valuation(
        self,
        metrics: FinancialMetrics,
        public_comps: List[Dict],
    ) -> Dict[str, Any]:
        """Analyze valuation relative to peers."""
        analysis = {"score": 0, "details": [], "metrics": {}}
        score = 50
        
        if not public_comps:
            analysis["details"].append("No public comps available for valuation comparison")
            return analysis
        
        # Compare EV/Revenue
        if metrics.ev_revenue and metrics.revenue:
            ev_rev = metrics.ev_revenue.value
            analysis["metrics"]["ev_revenue"] = ev_rev
            
            comp_ev_revs = [c.get("ev_revenue") for c in public_comps if c.get("ev_revenue")]
            if comp_ev_revs:
                median_comp = sorted(comp_ev_revs)[len(comp_ev_revs) // 2]
                analysis["metrics"]["median_comp_ev_revenue"] = median_comp
                
                if ev_rev < median_comp * 0.8:
                    score += 15
                    analysis["details"].append(f"Trading at discount to peers: {ev_rev:.1f}x vs {median_comp:.1f}x")
                elif ev_rev > median_comp * 1.5:
                    score -= 15
                    analysis["details"].append(f"Trading at premium to peers: {ev_rev:.1f}x vs {median_comp:.1f}x")
        
        analysis["score"] = max(0, min(100, score))
        return analysis
    
    def _analyze_growth_sustainability(
        self,
        financials: List[Dict],
        company_profile: Dict,
        metrics: FinancialMetrics,
    ) -> Dict[str, Any]:
        """Analyze sustainability of growth."""
        analysis = {"score": 0, "details": [], "metrics": {}}
        score = 50
        
        # Market size indicators
        tam = company_profile.get("tam")
        if tam:
            analysis["metrics"]["tam"] = tam
            if tam > 10_000_000_000:
                score += 15
            elif tam > 1_000_000_000:
                score += 10
        
        # Competitive advantages
        advantages = company_profile.get("competitive_advantages", [])
        if advantages:
            analysis["metrics"]["competitive_advantages"] = advantages
            score += min(15, len(advantages) * 5)
        
        # Recurring revenue (would need more data)
        analysis["details"].append("Recurring revenue analysis requires detailed revenue breakdown")
        
        analysis["score"] = max(0, min(100, score))
        return analysis
    
    def _calculate_scores(self, *analyses) -> Dict[str, float]:
        """Calculate weighted pillar scores."""
        weights = {
            "revenue": 0.25,
            "profitability": 0.25,
            "balance_sheet": 0.20,
            "cash_flow": 0.15,
            "valuation": 0.10,
            "growth": 0.05,
        }
        
        pillar_names = [
            "revenue_analysis",
            "profitability_analysis",
            "balance_sheet_analysis",
            "cash_flow_analysis",
            "valuation_analysis",
            "growth_analysis",
        ]
        
        scores = {}
        for name, analysis in zip(pillar_names, analyses):
            key = name.replace("_analysis", "")
            scores[key] = analysis.get("score", 0) * weights.get(key, 0.1)
        
        return scores
    
    def _calculate_confidence(
        self,
        financials: List[Dict],
        metrics: FinancialMetrics,
    ) -> float:
        """Calculate confidence based on data quality."""
        confidence = 0.5
        
        # More periods = higher confidence
        if len(financials) >= 8:
            confidence += 0.2
        elif len(financials) >= 4:
            confidence += 0.1
        
        # Key metrics availability
        key_metrics = [
            metrics.revenue,
            metrics.gross_margin,
            metrics.operating_margin,
            metrics.net_income,
            metrics.free_cash_flow,
            metrics.total_debt,
            metrics.cash_and_equivalents,
        ]
        available = sum(1 for m in key_metrics if m is not None)
        confidence += (available / len(key_metrics)) * 0.3
        
        return min(1.0, confidence)
    
    def _extract_key_metrics(self, metrics: FinancialMetrics) -> Dict[str, Any]:
        """Extract key metrics for reporting."""
        return {
            "revenue": float(metrics.revenue.amount) if metrics.revenue else None,
            "revenue_growth_yoy": metrics.revenue_growth_yoy.to_percent() if metrics.revenue_growth_yoy else None,
            "gross_margin": metrics.gross_margin.to_percent() if metrics.gross_margin else None,
            "operating_margin": metrics.operating_margin.to_percent() if metrics.operating_margin else None,
            "net_margin": metrics.net_margin.to_percent() if metrics.net_margin else None,
            "ebitda_margin": metrics.ebitda_margin.to_percent() if metrics.ebitda_margin else None,
            "free_cash_flow": float(metrics.free_cash_flow.amount) if metrics.free_cash_flow else None,
            "fcf_margin": metrics.fcf_margin.to_percent() if metrics.fcf_margin else None,
            "cash": float(metrics.cash_and_equivalents.amount) if metrics.cash_and_equivalents else None,
            "total_debt": float(metrics.total_debt.amount) if metrics.total_debt else None,
            "debt_to_equity": metrics.debt_to_equity.value if metrics.debt_to_equity else None,
            "current_ratio": metrics.current_ratio.value if metrics.current_ratio else None,
            "roe": metrics.roe.to_percent() if metrics.roe else None,
            "roic": metrics.roic.to_percent() if metrics.roic else None,
        }
    
    def _identify_strengths(self, *analyses) -> List[str]:
        """Identify key strengths from analyses."""
        strengths = []
        for analysis in analyses:
            if analysis.get("score", 0) > 70:
                pillar = analysis.get("pillar", "")
                strengths.append(f"Strong {pillar.replace('_', ' ')}")
        return strengths
    
    def _identify_weaknesses(self, *analyses) -> List[str]:
        """Identify key weaknesses from analyses."""
        weaknesses = []
        for analysis in analyses:
            if analysis.get("score", 0) < 40:
                pillar = analysis.get("pillar", "")
                weaknesses.append(f"Weak {pillar.replace('_', ' ')}")
        return weaknesses
    
    def _identify_red_flags(
        self,
        metrics: FinancialMetrics,
        financials: List[Dict],
    ) -> List[str]:
        """Identify red flags."""
        flags = []
        
        if metrics.net_income and metrics.net_income.amount < 0:
            flags.append("Negative net income")
        
        if metrics.free_cash_flow and metrics.free_cash_flow.amount < 0:
            flags.append("Negative free cash flow")
        
        if metrics.total_debt and metrics.cash_and_equivalents:
            if metrics.total_debt.amount > metrics.cash_and_equivalents.amount * 3:
                flags.append("Debt significantly exceeds cash")
        
        if metrics.current_ratio and metrics.current_ratio.value < 1:
            flags.append("Current ratio below 1.0")
        
        # Declining margins
        if len(financials) >= 2:
            latest_gm = financials[0].get("gross_margin")
            prev_gm = financials[1].get("gross_margin")
            if latest_gm and prev_gm and latest_gm < prev_gm - 0.05:
                flags.append("Gross margin declining >500bps QoQ")
        
        return flags
    
    def _generate_reasoning(self, result: Dict) -> str:
        """Generate human-readable reasoning."""
        parts = [
            f"Fundamental Analysis Score: {result['overall_score']:.1f}/100",
            f"Confidence: {result['confidence']:.0%}",
            "",
            "Pillar Scores:",
        ]
        
        for pillar, score in result["pillar_scores"].items():
            parts.append(f"  - {pillar.replace('_', ' ').title()}: {score:.1f}")
        
        if result["strengths"]:
            parts.append("\nKey Strengths:")
            for s in result["strengths"]:
                parts.append(f"  + {s}")
        
        if result["weaknesses"]:
            parts.append("\nKey Weaknesses:")
            for w in result["weaknesses"]:
                parts.append(f"  - {w}")
        
        if result["red_flags"]:
            parts.append("\n🚩 Red Flags:")
            for flag in result["red_flags"]:
                parts.append(f"  ⚠ {flag}")
        
        return "\n".join(parts)
    
    def _collect_evidence(
        self,
        metrics: FinancialMetrics,
        financials: List[Dict],
    ) -> List[str]:
        """Collect evidence citations."""
        evidence = []
        
        if metrics.revenue:
            evidence.append(f"Revenue: ${metrics.revenue.amount:,.0f}")
        if metrics.revenue_growth_yoy:
            evidence.append(f"YoY Growth: {metrics.revenue_growth_yoy.to_percent():.1f}%")
        if metrics.gross_margin:
            evidence.append(f"Gross Margin: {metrics.gross_margin.to_percent():.1f}%")
        if metrics.operating_margin:
            evidence.append(f"Operating Margin: {metrics.operating_margin.to_percent():.1f}%")
        if metrics.free_cash_flow:
            evidence.append(f"FCF: ${metrics.free_cash_flow.amount:,.0f}")
        if metrics.cash_and_equivalents:
            evidence.append(f"Cash: ${metrics.cash_and_equivalents.amount:,.0f}")
        if metrics.total_debt:
            evidence.append(f"Total Debt: ${metrics.total_debt.amount:,.0f}")
        
        evidence.append(f"Periods analyzed: {len(financials)}")
        
        return evidence