"""Report Generation Agent - Creates comprehensive investment research reports."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, InvestmentStrategy, RiskLevel, TimeHorizon
from app.domain.entities.entities import OverallAnalysis, Report
from app.domain.value_objects.value_objects import InvestmentThesis, Money, Percentage
from app.core.exceptions.base import AgentError


class ReportGenerationAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that generates professional investment research reports."""

    def __init__(self):
        super().__init__(
            name=AgentName.REPORT,
            description="Generates comprehensive investment research reports from analysis results",
            version="1.0.0",
            max_retries=1,
            timeout_seconds=120,
        )

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
- Include standard disclaimers"""

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

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Generate comprehensive investment research report."""
        start_time = datetime.utcnow()

        try:
            # Extract all analysis results
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

            # Generate report sections
            sections = {}
            sections["executive_summary"] = self._render_executive_summary(
                overall_analysis, fundamental, market, risk, sentiment, ipo_details
            )
            sections["ipo_overview"] = self._render_ipo_overview(ipo_details, company_profile)
            sections["company_background"] = self._render_company_background(company_profile, ipo_details)
            sections["industry_analysis"] = self._render_industry_analysis(market, company_profile)
            sections["financial_analysis"] = self._render_financial_analysis(fundamental, financials, public_comps)
            sections["valuation_analysis"] = self._render_valuation_analysis(fundamental, market, public_comps, ipo_details)
            sections["risk_analysis"] = self._render_risk_analysis(risk, fundamental, market)
            sections["management_assessment"] = self._render_management_assessment(company_profile, ipo_details)
            sections["sentiment_analysis"] = self._render_sentiment_analysis(sentiment)
            sections["investment_thesis"] = self._render_investment_thesis(overall_analysis, fundamental, market, risk)
            sections["recommendation"] = self._render_recommendation(overall_analysis)

            # Build full report
            report_content = self._assemble_report(sections, symbol, overall_analysis)

            # Generate structured data for UI
            key_metrics = self._extract_key_metrics(fundamental, market, risk, sentiment, overall_analysis)
            financial_tables = self._generate_financial_tables(financials, public_comps)
            charts = self._generate_chart_configs(fundamental, market, risk, sentiment)
            sources = self._compile_sources(financials, market, risk, sentiment, ipo_details)
            disclaimers = self._get_standard_disclaimers()

            # Create report entity
            report = Report(
                ipo_id=analysis_id,
                analysis_id=analysis_id,
                title=f"{symbol} - IPO Investment Research Report",
                executive_summary=sections["executive_summary"],
                ipo_overview=sections["ipo_overview"],
                company_background=sections["company_background"],
                industry_analysis=sections["industry_analysis"],
                financial_analysis=sections["financial_analysis"],
                valuation_analysis=sections["valuation_analysis"],
                risk_analysis=sections["risk_analysis"],
                management_assessment=sections["management_assessment"],
                sentiment_analysis=sections["sentiment_analysis"],
                bull_case=sections["investment_thesis"].get("bull_case", ""),
                bear_case=sections["investment_thesis"].get("bear_case", ""),
                investment_thesis=sections["investment_thesis"].get("full_thesis", ""),
                recommendation=sections["recommendation"],
                key_metrics=key_metrics,
                financial_tables=financial_tables,
                charts=charts,
                sources=sources,
                disclaimers=disclaimers,
                generated_by="ReportGenerationAgent v1.0.0",
                model_version="1.0.0",
            )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data={
                    "report": report.to_dict() if hasattr(report, 'to_dict') else report.__dict__,
                    "markdown": report_content,
                    "sections": sections,
                    "key_metrics": key_metrics,
                    "financial_tables": financial_tables,
                    "charts": charts,
                    "sources": sources,
                },
                confidence=overall_analysis.get("confidence", 0.7),
                reasoning=self._generate_reasoning(overall_analysis),
                evidence=self._collect_evidence(sections),
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

    def _render_executive_summary(
        self,
        overall: Dict,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
        ipo_details: Dict,
    ) -> str:
        """Render executive summary section."""
        symbol = ipo_details.get("symbol", "N/A")
        company_name = ipo_details.get("company_name", "N/A")
        score = overall.get("overall_score", 0)
        recommendation = overall.get("investment_strategy", "WATCH")
        confidence = overall.get("confidence", 0)
        risk_level = overall.get("risk_level", "MODERATE")

        rec_text = self._get_recommendation_text(recommendation)

        parts = [
            f"# Executive Summary: {company_name} ({symbol})",
            "",
            f"**Recommendation:** {recommendation} | **Score:** {score:.1f}/100 | **Confidence:** {confidence:.0%} | **Risk:** {risk_level}",
            "",
            "## Key Investment Highlights",
        ]

        # Add top strengths
        strengths = fundamental.get("strengths", [])
        if strengths:
            parts.append("**Strengths:**")
            for s in strengths[:3]:
                parts.append(f"  • {s}")

        # Add top risks
        key_risks = overall.get("key_risks", [])
        if key_risks:
            parts.append("\n**Key Risks:**")
            for r in key_risks[:3]:
                parts.append(f"  • {r}")

        # Add catalysts
        catalysts = overall.get("key_catalysts", [])
        if catalysts:
            parts.append("\n**Near-term Catalysts:**")
            for c in catalysts[:3]:
                parts.append(f"  • {c}")

        # IPO details
        parts.extend([
            "",
            "## IPO Details",
            f"- **Expected Date:** {ipo_details.get('expected_date', 'TBD')}",
            f"- **Exchange:** {ipo_details.get('exchange', 'TBD')}",
            f"- **Price Range:** {ipo_details.get('price_range', 'Not disclosed')}",
            f"- **Shares Offered:** {ipo_details.get('shares_offered', 'TBD')}",
            f"- **Lead Underwriters:** {', '.join(ipo_details.get('underwriters', ['TBD'])[:3])}",
            f"- **Use of Proceeds:** {ipo_details.get('use_of_proceeds', 'General corporate purposes')}",
        ])

        # Score breakdown
        parts.extend([
            "",
            "## Score Breakdown",
            f"- **Financial Strength:** {overall.get('financial_strength_score', 0):.1f}/100",
            f"- **Growth Potential:** {overall.get('growth_potential_score', 0):.1f}/100",
            f"- **Market Opportunity:** {overall.get('market_opportunity_score', 0):.1f}/100",
            f"- **Management Quality:** {overall.get('management_quality_score', 0):.1f}/100",
            f"- **Risk Level (inverted):** {100 - overall.get('risk_level_score', 50):.1f}/100",
        ])

        return "\n".join(parts)

    def _render_ipo_overview(self, ipo_details: Dict, company_profile: Dict) -> str:
        """Render IPO overview section."""
        parts = [
            "# IPO Overview",
            "",
            "## Offering Structure",
        ]

        # Offer details
        price_low = ipo_details.get("expected_price_low")
        price_high = ipo_details.get("expected_price_high")
        if price_low and price_high:
            parts.append(f"- **Price Range:** ${price_low:.2f} - ${price_high:.2f}")
            mid = (price_low + price_high) / 2
            parts.append(f"- **Midpoint:** ${mid:.2f}")

        parts.extend([
            f"- **Shares Offered:** {ipo_details.get('shares_offered', 'N/A'):,}",
            f"- **Total Offer Size:** ${ipo_details.get('expected_raise', 0):,.0f}" if ipo_details.get('expected_raise') else "- **Total Offer Size:** TBD",
            f"- **Overallotment Option:** {'Yes' if ipo_details.get('greenshoe_option') else 'No'}",
        ])

        if ipo_details.get("greenshoe_shares"):
            parts.append(f"- **Overallotment Shares:** {ipo_details['greenshoe_shares']:,}")

        # Valuation
        parts.extend([
            "",
            "## Implied Valuation",
        ])
        if ipo_details.get("expected_valuation_low") and ipo_details.get("expected_valuation_high"):
            parts.append(f"- **Pre-Money Valuation:** ${ipo_details['expected_valuation_low']:,.0f} - ${ipo_details['expected_valuation_high']:,.0f}")
        if ipo_details.get("post_money_valuation"):
            parts.append(f"- **Post-Money Valuation:** ${ipo_details['post_money_valuation']:,.0f}")

        # Underwriters
        parts.extend([
            "",
            "## Underwriting Syndicate",
            f"- **Lead Underwriters:** {', '.join(ipo_details.get('lead_underwriters', ['TBD']))}",
        ])
        if ipo_details.get("co_managers"):
            parts.append(f"- **Co-Managers:** {', '.join(ipo_details['co_managers'])}")

        # Lockup
        parts.extend([
            "",
            "## Lockup & Ownership",
        ])
        if ipo_details.get("lockup_expiry"):
            parts.append(f"- **Lockup Expiry:** {ipo_details['lockup_expiry']}")
        if ipo_details.get("lockup_days"):
            parts.append(f"- **Lockup Period:** {ipo_details['lockup_days']} days")
        if ipo_details.get("insider_shares_pct"):
            parts.append(f"- **Insider Ownership (post-IPO):** {ipo_details['insider_shares_pct']:.1%}")

        return "\n".join(parts)

    def _render_company_background(self, company_profile: Dict, ipo_details: Dict) -> str:
        """Render company background section."""
        parts = [
            "# Company Background",
            "",
            f"## Overview",
            company_profile.get("description", "Company description not available."),
            "",
            "## Business Model",
            company_profile.get("business_model", "Business model details not available."),
            "",
            "## Key Products & Services",
        ]

        products = company_profile.get("key_products", [])
        if products:
            for p in products:
                parts.append(f"  • {p}")
        else:
            parts.append("  Product details not available.")

        parts.extend([
            "",
            "## Target Markets",
        ])
        markets = company_profile.get("target_markets", [])
        if markets:
            for m in markets:
                parts.append(f"  • {m}")
        else:
            parts.append("  Target market details not available.")

        parts.extend([
            "",
            "## Competitive Advantages",
        ])
        advantages = company_profile.get("competitive_advantages", [])
        if advantages:
            for a in advantages:
                parts.append(f"  • {a}")
        else:
            parts.append("  Competitive advantages not disclosed.")

        parts.extend([
            "",
            "## Management Team",
        ])
        if company_profile.get("ceo"):
            parts.append(f"- **CEO:** {company_profile['ceo']}")
        if company_profile.get("cfo"):
            parts.append(f"- **CFO:** {company_profile['cfo']}")
        if company_profile.get("coo"):
            parts.append(f"- **COO:** {company_profile['coo']}")

        board = company_profile.get("board_members", [])
        if board:
            parts.append(f"- **Board Members:** {', '.join(board[:5])}")

        parts.extend([
            "",
            "## Company History",
            f"- **Founded:** {company_profile.get('founded_year', 'N/A')}",
            f"- **Headquarters:** {company_profile.get('headquarters', 'N/A')}",
            f"- **Employees:** {company_profile.get('employee_count', 'N/A'):,}" if company_profile.get('employee_count') else "- **Employees:** N/A",
            f"- **Website:** {company_profile.get('website', 'N/A')}",
        ])

        return "\n".join(parts)

    def _render_industry_analysis(self, market: Dict, company_profile: Dict) -> str:
        """Render industry analysis section."""
        parts = [
            "# Industry Analysis",
            "",
            "## Market Opportunity",
        ]

        tam = market.get("tam_analysis", {})
        sam = market.get("sam_analysis", {})
        som = market.get("som_analysis", {})

        if tam.get("tam_usd"):
            parts.append(f"- **Total Addressable Market (TAM):** ${tam['tam_usd']/1e9:.1f}B")
            parts.append(f"  - Methodology: {tam.get('methodology', 'Industry estimates')}")
            parts.append(f"  - CAGR: {tam.get('cagr', 0):.1%}")

        if sam.get("sam_usd"):
            parts.append(f"- **Serviceable Addressable Market (SAM):** ${sam['sam_usd']/1e9:.1f}B")
            parts.append(f"  - SAM/TAM Ratio: {sam.get('sam_tam_ratio', 0):.1%}")

        if som.get("som_usd"):
            parts.append(f"- **Serviceable Obtainable Market (SOM):** ${som['som_usd']/1e6:.0f}M")
            parts.append(f"  - Projected Market Share: {som.get('projected_market_share', 0):.1%}")

        parts.extend([
            "",
            "## Market Trends & Drivers",
        ])
        trends = market.get("trends_analysis", {})
        tailwinds = trends.get("tailwinds", [])
        headwinds = trends.get("headwinds", [])

        if tailwinds:
            parts.append("**Tailwinds:**")
            for t in tailwinds[:5]:
                parts.append(f"  • {t}")

        if headwinds:
            parts.append("\n**Headwinds:**")
            for h in headwinds[:5]:
                parts.append(f"  • {h}")

        parts.extend([
            "",
            "## Competitive Landscape",
        ])
        comp = market.get("competitive_analysis", {})
        if comp:
            parts.append(f"- **Competitive Intensity:** {comp.get('intensity', 'Unknown').title()}")
            parts.append(f"- **Total Competitors:** {comp.get('total_competitors', 0)}")
            parts.append(f"- **Direct Competitors:** {comp.get('direct_competitors', 0)}")
            parts.append(f"- **Public Competitors:** {comp.get('public_competitors', 0)}")
            parts.append(f"- **Moat Strength:** {comp.get('moat_strength', 'Unknown').title()}")
            parts.append(f"- **Market Structure:** {comp.get('market_structure', 'Unknown').title()}")

            key_comp = comp.get("key_competitors", [])
            if key_comp:
                parts.append("\n**Key Competitors:**")
                for c in key_comp[:5]:
                    parts.append(f"  • {c.get('name', 'N/A')} - {'Public' if c.get('public') else 'Private'} - Rev: ${c.get('estimated_revenue', 0):,.0f}" if c.get('estimated_revenue') else f"  • {c.get('name', 'N/A')} - {'Public' if c.get('public') else 'Private'}")

        parts.extend([
            "",
            "## Positioning & Differentiation",
        ])
        positioning = market.get("positioning_analysis", {})
        if positioning:
            parts.append(f"- **Differentiation:** {positioning.get('differentiation', 'Not specified')}")
            parts.append(f"- **Value Proposition:** {positioning.get('value_proposition', 'Not specified')}")
            parts.append(f"- **Switching Costs:** {positioning.get('switching_costs', 'Unknown').title()}")
            parts.append(f"- **Network Effects:** {'Yes' if positioning.get('network_effects') else 'No'}")
            parts.append(f"- **Brand Strength:** {positioning.get('brand_strength', 'Unknown').title()}")

        return "\n".join(parts)

    def _render_financial_analysis(
        self,
        fundamental: Dict,
        financials: Dict,
        public_comps: List,
    ) -> str:
        """Render financial analysis section."""
        parts = [
            "# Financial Analysis",
            "",
            "## Historical Financial Performance",
        ]

        statements = financials.get("statements", [])
        if statements:
            latest = statements[0]
            parts.extend([
                f"### Latest Period ({latest.get('period', 'N/A')})",
                f"- **Revenue:** ${latest.get('revenue', 0):,.0f}",
                f"- **YoY Growth:** {latest.get('revenue_growth_yoy', 0):.1%}",
                f"- **Gross Profit:** ${latest.get('gross_profit', 0):,.0f}",
                f"- **Gross Margin:** {latest.get('gross_margin', 0):.1%}",
                f"- **Operating Income:** ${latest.get('operating_income', 0):,.0f}",
                f"- **Operating Margin:** {latest.get('operating_margin', 0):.1%}",
                f"- **Net Income:** ${latest.get('net_income', 0):,.0f}",
                f"- **Net Margin:** {latest.get('net_margin', 0):.1%}",
                f"- **EBITDA:** ${latest.get('ebitda', 0):,.0f}",
                f"- **EBITDA Margin:** {latest.get('ebitda_margin', 0):.1%}",
                f"- **Free Cash Flow:** ${latest.get('free_cash_flow', 0):,.0f}",
                f"- **FCF Margin:** {latest.get('fcf_margin', 0):.1%}",
            ])
        else:
            parts.append("Financial statements not available.")

        parts.extend([
            "",
            "## Key Financial Ratios",
        ])

        metrics = fundamental.get("key_metrics", {})
        if metrics:
            ratio_items = [
                ("Debt/Equity", metrics.get("debt_to_equity"), "x"),
                ("Current Ratio", metrics.get("current_ratio"), "x"),
                ("ROE", metrics.get("roe"), "%"),
                ("ROIC", metrics.get("roic"), "%"),
                ("P/E", metrics.get("pe_ratio"), "x"),
                ("EV/Revenue", metrics.get("ev_revenue"), "x"),
                ("EV/EBITDA", metrics.get("ev_ebitda"), "x"),
            ]
            for name, value, unit in ratio_items:
                if value is not None:
                    if unit == "%":
                        parts.append(f"- **{name}:** {value:.1f}%")
                    else:
                        parts.append(f"- **{name}:** {value:.2f}x")
        else:
            parts.append("Financial ratios not available.")

        parts.extend([
            "",
            "## Balance Sheet Strength",
        ])
        if statements:
            latest = statements[0]
            parts.extend([
                f"- **Cash & Equivalents:** ${latest.get('cash_and_equivalents', 0):,.0f}",
                f"- **Total Debt:** ${latest.get('total_debt', 0):,.0f}",
                f"- **Net Cash/(Debt):** ${latest.get('cash_and_equivalents', 0) - latest.get('total_debt', 0):,.0f}",
                f"- **Total Equity:** ${latest.get('total_equity', 0):,.0f}",
                f"- **Working Capital:** ${latest.get('working_capital', 0):,.0f}",
            ])

        parts.extend([
            "",
            "## Cash Flow Analysis",
        ])
        if statements:
            latest = statements[0]
            parts.extend([
                f"- **Operating Cash Flow:** ${latest.get('operating_cash_flow', 0):,.0f}",
                f"- **CapEx:** ${latest.get('capex', 0):,.0f}",
                f"- **Free Cash Flow:** ${latest.get('free_cash_flow', 0):,.0f}",
                f"- **FCF Conversion:** {latest.get('fcf_conversion', 0):.1%}" if latest.get('fcf_conversion') else "- **FCF Conversion:** N/A",
            ])

        parts.extend([
            "",
            "## Peer Comparison",
        ])
        if public_comps:
            parts.append("| Company | Market Cap | EV/Rev | EV/EBITDA | P/E | Rev Growth | Margin |")
            parts.append("|---------|------------|--------|-----------|-----|------------|--------|")
            for comp in public_comps[:5]:
                parts.append(
                    f"| {comp.get('symbol', 'N/A')} | "
                    f"${comp.get('market_cap', 0)/1e9:.1f}B | "
                    f"{comp.get('ev_revenue', 0):.1f}x | "
                    f"{comp.get('ev_ebitda', 0):.1f}x | "
                    f"{comp.get('pe_ratio', 0):.1f}x | "
                    f"{comp.get('revenue_growth', 0):.1%} | "
                    f"{comp.get('profit_margin', 0):.1%} |"
                )
        else:
            parts.append("Peer comparison data not available.")

        # Red flags
        red_flags = fundamental.get("red_flags", [])
        if red_flags:
            parts.extend([
                "",
                "## ⚠️ Red Flags",
            ])
            for flag in red_flags:
                parts.append(f"  • {flag}")

        return "\n".join(parts)

    def _render_valuation_analysis(
        self,
        fundamental: Dict,
        market: Dict,
        public_comps: List,
        ipo_details: Dict,
    ) -> str:
        """Render valuation analysis section."""
        parts = [
            "# Valuation Analysis",
            "",
            "## IPO Valuation",
        ]

        price_low = ipo_details.get("expected_price_low")
        price_high = ipo_details.get("expected_price_high")
        if price_low and price_high:
            parts.append(f"- **Offer Price Range:** ${price_low:.2f} - ${price_high:.2f}")
            mid = (price_low + price_high) / 2
            parts.append(f"- **Midpoint:** ${mid:.2f}")

        if ipo_details.get("expected_valuation_low") and ipo_details.get("expected_valuation_high"):
            parts.append(f"- **Implied Enterprise Value:** ${ipo_details['expected_valuation_low']:,.0f} - ${ipo_details['expected_valuation_high']:,.0f}")

        parts.extend([
            "",
            "## Comparable Company Analysis",
        ])

        if public_comps:
            ev_rev = [c.get("ev_revenue") for c in public_comps if c.get("ev_revenue")]
            ev_ebitda = [c.get("ev_ebitda") for c in public_comps if c.get("ev_ebitda")]
            pe = [c.get("pe_ratio") for c in public_comps if c.get("pe_ratio")]

            if ev_rev:
                parts.append(f"- **Median EV/Revenue:** {sorted(ev_rev)[len(ev_rev)//2]:.1f}x")
            if ev_ebitda:
                parts.append(f"- **Median EV/EBITDA:** {sorted(ev_ebitda)[len(ev_ebitda)//2]:.1f}x")
            if pe:
                parts.append(f"- **Median P/E:** {sorted(pe)[len(pe)//2]:.1f}x")

            # Implied valuation at comp multiples
            revenue = fundamental.get("key_metrics", {}).get("revenue")
            if revenue and ev_rev:
                median_ev_rev = sorted(ev_rev)[len(ev_rev)//2]
                implied_ev = revenue * median_ev_rev
                parts.append(f"- **Implied EV at Median EV/Rev:** ${implied_ev:,.0f}")

        parts.extend([
            "",
            "## Discounted Cash Flow (Framework)",
            "A full DCF model would require detailed projections. Key assumptions would include:",
            "- **Revenue CAGR (5Y):** Based on market growth and company-specific factors",
            "- **Terminal Growth Rate:** 2-3% (GDP growth)",
            "- **WACC:** 10-12% (adjusted for company risk profile)",
            "- **Target Operating Margin:** Based on peer maturity and company trajectory",
            "",
            "## Valuation Assessment",
        ])

        val_analysis = fundamental.get("valuation_analysis", {})
        if val_analysis:
            score = val_analysis.get("score", 50)
            if score > 70:
                parts.append("IPO appears **attractively valued** relative to peers and growth prospects.")
            elif score > 50:
                parts.append("IPO appears **fairly valued** with balanced risk/reward.")
            else:
                parts.append("IPO appears **richly valued** with limited margin of safety.")

            details = val_analysis.get("details", [])
            for d in details:
                parts.append(f"  • {d}")

        return "\n".join(parts)

    def _render_risk_analysis(
        self,
        risk: Dict,
        fundamental: Dict,
        market: Dict,
    ) -> str:
        """Render risk analysis section."""
        parts = [
            "# Risk Analysis",
            "",
            f"## Overall Risk Level: {risk.get('overall_risk_level', 'MODERATE').upper()}",
            f"**Risk Score:** {risk.get('overall_risk_score', 50):.1f}/100",
            f"**Total Risks Identified:** {risk.get('risk_count', 0)}",
            f"**High Priority Risks:** {risk.get('high_priority_risks', 0)}",
            "",
            "## Top 10 Risks",
        ]

        top_risks = risk.get("top_risks", [])
        for i, r in enumerate(top_risks[:10], 1):
            parts.append(
                f"### {i}. [{r.get('severity', 'MODERATE').upper()}] {r.get('category', 'General')}: {r.get('factor', 'N/A')}"
            )
            parts.append(f"   - **Probability:** {r.get('probability', 0):.0%}")
            parts.append(f"   - **Impact:** {r.get('impact', 0):.0%}")
            parts.append(f"   - **Risk Score:** {r.get('risk_score', 0):.1f}")
            parts.append(f"   - **Description:** {r.get('description', 'N/A')}")
            evidence = r.get('evidence', [])
            if evidence:
                parts.append(f"   - **Evidence:** {'; '.join(evidence)}")
            mitigation = r.get('mitigation', '')
            if mitigation:
                parts.append(f"   - **Mitigation:** {mitigation}")
            parts.append("")

        # Risk by category
        by_category = risk.get("risk_by_category", {})
        if by_category:
            parts.append("## Risks by Category")
            for cat, risks in by_category.items():
                high_sev = [r for r in risks if r.get('severity') in ['HIGH', 'VERY_HIGH', 'EXTREME']]
                parts.append(f"\n**{cat}** ({len(risks)} risks, {len(high_sev)} high severity)")
                for r in risks[:3]:
                    parts.append(f"  • {r.get('factor', 'N/A')} [{r.get('severity', 'MODERATE')}]")

        # Red flags
        red_flags = risk.get("red_flags", [])
        if red_flags:
            parts.extend([
                "",
                "## 🚩 Critical Red Flags",
            ])
            for flag in red_flags:
                parts.append(f"  • {flag}")

        # Scenarios
        scenarios = risk.get("scenarios", {})
        if scenarios:
            parts.extend([
                "",
                "## Scenario Analysis",
            ])
            for name, scenario in scenarios.items():
                parts.append(f"\n### {name.title()} Case (Probability: {scenario.get('probability', 0):.0%})")
                parts.append(f"- **Revenue Impact:** {scenario.get('revenue', 0):,.0f}")
                parts.append(f"- **FCF Impact:** {scenario.get('fcf', 0):,.0f}")
                if scenario.get("key_risks"):
                    parts.append(f"- **Key Risks:** {', '.join(scenario['key_risks'])}")

        return "\n".join(parts)

    def _render_management_assessment(
        self,
        company_profile: Dict,
        ipo_details: Dict,
    ) -> str:
        """Render management assessment section."""
        parts = [
            "# Management Assessment",
            "",
            "## Leadership Team",
        ]

        if company_profile.get("ceo"):
            parts.append(f"- **CEO:** {company_profile['ceo']}")
        if company_profile.get("cfo"):
            parts.append(f"- **CFO:** {company_profile['cfo']}")
        if company_profile.get("coo"):
            parts.append(f"- **COO:** {company_profile['coo']}")

        key_people = company_profile.get("key_people", [])
        if key_people:
            parts.append("\n**Other Key Executives:**")
            for p in key_people[:5]:
                parts.append(f"  • {p.get('name', 'N/A')} - {p.get('title', 'N/A')}")

        parts.extend([
            "",
            "## Board of Directors",
        ])
        board = company_profile.get("board_members", [])
        if board:
            independent = sum(1 for b in board if isinstance(b, dict) and b.get("independent"))
            total = len(board)
            parts.append(f"- **Board Size:** {total} directors")
            parts.append(f"- **Independent Directors:** {independent} ({independent/total:.0%})" if total > 0 else "")
            for b in board[:7]:
                if isinstance(b, dict):
                    parts.append(f"  • {b.get('name', 'N/A')} - {'Independent' if b.get('independent') else 'Affiliated'}")
                else:
                    parts.append(f"  • {b}")

        parts.extend([
            "",
            "## Governance Structure",
        ])
        share_structure = ipo_details.get("share_structure", {})
        if share_structure.get("dual_class"):
            parts.append("⚠️ **Dual-Class Share Structure** - Insiders retain voting control")
            parts.append(f"   - Insider Voting Control: {share_structure.get('insider_voting_pct', 'N/A')}%")
        else:
            parts.append("✓ Single-class share structure")

        insider_control = share_structure.get("insider_voting_pct", 0)
        if insider_control > 50:
            parts.append(f"- **Insider Voting Control:** {insider_control:.0f}%")

        parts.extend([
            "",
            "## Ownership & Alignment",
        ])
        if ipo_details.get("insider_shares_pct"):
            parts.append(f"- **Post-IPO Insider Ownership:** {ipo_details['insider_shares_pct']:.1%}")

        major_shareholders = company_profile.get("major_shareholders", {})
        if major_shareholders:
            parts.append("- **Major Pre-IPO Shareholders:**")
            for name, pct in list(major_shareholders.items())[:5]:
                parts.append(f"  • {name}: {pct:.1%}")

        parts.extend([
            "",
            "## Assessment Summary",
            "Management team assessment based on experience, track record, and alignment:",
        ])

        # Simple scoring
        exp_score = 50
        if company_profile.get("ceo"):
            exp_score += 10
        if company_profile.get("cfo"):
            exp_score += 10
        if len(board) >= 5:
            exp_score += 10
        if independent / max(total, 1) > 0.5:
            exp_score += 10
        if not share_structure.get("dual_class"):
            exp_score += 10

        parts.append(f"- **Management Quality Score:** {min(100, exp_score)}/100")

        return "\n".join(parts)

    def _render_sentiment_analysis(self, sentiment: Dict) -> str:
        """Render sentiment analysis section."""
        parts = [
            "# Sentiment Analysis",
            "",
            f"## Composite Sentiment: {sentiment.get('composite_label', 'NEUTRAL').upper()}",
            f"**Score:** {sentiment.get('composite_score', 0):.2f} (-1 to +1)",
            f"**Confidence:** {sentiment.get('confidence', 0):.0%}",
            "",
            "## Source Breakdown",
        ]

        breakdown = sentiment.get("source_breakdown", {})
        for source, data in breakdown.items():
            parts.append(
                f"- **{source.title()}:** {data.get('score', 0):.2f} ({data.get('label', 'NEUTRAL')}) "
                f"- Weight: {data.get('weight', 0):.0%} - {data.get('article_count', 0)} items"
            )

        parts.extend([
            "",
            "## Key Themes",
        ])

        pos_themes = sentiment.get("positive_themes", [])
        if pos_themes:
            parts.append("**Positive:**")
            for t in pos_themes:
                parts.append(f"  • {t}")

        neg_themes = sentiment.get("negative_themes", [])
        if neg_themes:
            parts.append("\n**Negative:**")
            for t in neg_themes:
                parts.append(f"  • {t}")

        divergences = sentiment.get("divergences", [])
        if divergences:
            parts.extend([
                "",
                "## ⚠️ Sentiment Divergences",
            ])
            for d in divergences:
                parts.append(f"- **{d.get('type', 'N/A')}:** {d.get('interpretation', 'N/A')} (Gap: {d.get('gap', 0):.2f})")

        momentum = sentiment.get("momentum", "stable")
        parts.extend([
            "",
            f"## Momentum: {momentum.replace('_', ' ').title()}",
        ])

        peer_comp = sentiment.get("peer_comparison", {})
        if peer_comp.get("available"):
            parts.extend([
                "",
                "## Peer Comparison",
                f"- **Our Score:** {peer_comp.get('our_score', 0):.2f}",
                f"- **Peer Average:** {peer_comp.get('peer_average', 0):.2f}",
                f"- **Percentile:** {peer_comp.get('percentile', 50)}th",
                f"- **Assessment:** {peer_comp.get('interpretation', 'N/A')}",
            ])

        quotes = sentiment.get("key_quotes", [])
        if quotes:
            parts.extend([
                "",
                "## Key Quotes",
            ])
            for q in quotes[:5]:
                parts.append(f"  • {q}")

        return "\n".join(parts)

    def _render_investment_thesis(
        self,
        overall: Dict,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
    ) -> Dict[str, str]:
        """Render investment thesis with bull/bear cases."""
        bull_case = overall.get("investment_thesis", {}).get("bull_case", "")
        bear_case = overall.get("investment_thesis", {}).get("bear_case", "")

        if not bull_case:
            bull_case = self._generate_bull_case(fundamental, market, overall)
        if not bear_case:
            bear_case = self._generate_bear_case(fundamental, market, risk)

        full_thesis = f"""## Investment Thesis

### Bull Case
{bull_case}

### Bear Case
{bear_case}

### Key Assumptions
{chr(10).join(f'  • {a}' for a in overall.get('investment_thesis', {}).get('assumptions', []))}
"""

        return {
            "bull_case": bull_case,
            "bear_case": bear_case,
            "full_thesis": full_thesis,
        }

    def _generate_bull_case(self, fundamental: Dict, market: Dict, overall: Dict) -> str:
        """Generate bull case narrative."""
        parts = []
        strengths = fundamental.get("strengths", [])
        if strengths:
            parts.append("**Fundamental Strengths:**")
            for s in strengths[:3]:
                parts.append(f"  • {s}")

        opps = market.get("key_opportunities", [])
        if opps:
            parts.append("\n**Market Opportunities:**")
            for o in opps[:3]:
                parts.append(f"  • {o}")

        comp = market.get("competitive_analysis", {})
        if comp.get("moat_strength") in ["strong", "moderate"]:
            parts.append(f"\n**Competitive Position:** {comp.get('moat_strength', '').title()} moat with {comp.get('switching_costs', 'moderate')} switching costs")

        catalysts = overall.get("key_catalysts", [])
        if catalysts:
            parts.append("\n**Positive Catalysts:**")
            for c in catalysts[:3]:
                parts.append(f"  • {c}")

        return "\n".join(parts) if parts else "Bull case under development."

    def _generate_bear_case(self, fundamental: Dict, market: Dict, risk: Dict) -> str:
        """Generate bear case narrative."""
        parts = []
        weaknesses = fundamental.get("weaknesses", [])
        if weaknesses:
            parts.append("**Fundamental Weaknesses:**")
            for w in weaknesses[:3]:
                parts.append(f"  • {w}")

        red_flags = fundamental.get("red_flags", [])
        if red_flags:
            parts.append("\n**Red Flags:**")
            for r in red_flags[:3]:
                parts.append(f"  • {r}")

        m_risks = market.get("key_risks", [])
        if m_risks:
            parts.append("\n**Market Risks:**")
            for r in m_risks[:3]:
                parts.append(f"  • {r}")

        risk_flags = risk.get("red_flags", [])
        if risk_flags:
            parts.append("\n**Critical Risks:**")
            for r in risk_flags[:3]:
                parts.append(f"  • {r}")

        return "\n".join(parts) if parts else "Bear case under development."

    def _render_recommendation(self, overall: Dict) -> str:
        """Render final recommendation section."""
        score = overall.get("overall_score", 0)
        recommendation = overall.get("investment_strategy", "WATCH")
        confidence = overall.get("confidence", 0)
        risk_level = overall.get("risk_level", "MODERATE")
        time_horizon = overall.get("time_horizon", "MEDIUM_TERM")

        parts = [
            "# Recommendation",
            "",
            f"## {recommendation.replace('_', ' ').upper()}",
            f"**Overall Score:** {score:.1f}/100",
            f"**Confidence:** {confidence:.0%}",
            f"**Risk Level:** {risk_level}",
            f"**Time Horizon:** {time_horizon.replace('_', ' ').title()}",
            "",
            "### Rationale",
        ]

        rec_text = self._get_recommendation_text(recommendation)
        parts.append(rec_text)

        parts.extend([
            "",
            "### Position Sizing Guidance",
        ])
        pos = overall.get("position_guidance", {})
        if pos:
            parts.append(f"- **Suggested Max Position:** {pos.get('suggested_max_pct', 'N/A')}% of portfolio")
            parts.append(f"- **Initial Entry:** {pos.get('suggested_entry_pct', 'N/A')}%")
            if pos.get("scaling_plan"):
                parts.append("- **Scaling Plan:**")
                for stage in pos["scaling_plan"]:
                    parts.append(f"  • {stage}")

        parts.extend([
            "",
            "### Entry Strategy",
        ])
        entry = overall.get("entry_strategy", {})
        if entry:
            parts.append(f"- **Strategy:** {entry.get('strategy', 'N/A').replace('_', ' ').title()}")
            if entry.get("trigger_conditions"):
                parts.append("- **Trigger Conditions:**")
                for t in entry["trigger_conditions"]:
                    parts.append(f"  • {t}")
            if entry.get("stop_loss"):
                parts.append(f"- **Stop Loss:** {entry['stop_loss']}")

        parts.extend([
            "",
            "### Monitoring Plan",
        ])
        monitoring = overall.get("monitoring_plan", {})
        if monitoring:
            for freq, items in monitoring.items():
                if items:
                    parts.append(f"**{freq.title()}:**")
                    for item in items[:3]:
                        parts.append(f"  • {item}")

        parts.extend([
            "",
            "---",
            "*This report is for informational purposes only and does not constitute investment advice. "
            "Past performance is not indicative of future results. Please consult with a qualified "
            "financial advisor before making investment decisions.*",
        ])

        return "\n".join(parts)

    def _get_recommendation_text(self, recommendation: str) -> str:
        """Get recommendation description."""
        descriptions = {
            "AGGRESSIVE_BUY": "Exceptional opportunity with highly favorable risk/reward. Strong fundamentals, large market opportunity, and competent management. Suitable for high-conviction allocation.",
            "BUY": "Attractive investment opportunity with solid fundamentals and manageable risks. Expected to outperform over the investment horizon.",
            "ACCUMULATE": "Good opportunity worth building a position in, preferably on weakness. Favorable long-term prospects with some near-term uncertainty.",
            "HOLD": "Fairly valued at current levels. Maintain existing position but not a compelling new entry point.",
            "WATCH": "Interesting story but premature for investment. Monitor for better entry point or catalyst confirmation.",
            "REDUCE": "Consider trimming position on strength. Risk/reward has deteriorated or valuation has become stretched.",
            "SELL": "Unfavorable risk/reward profile. Significant fundamental deterioration or overvaluation.",
            "AVOID": "High risk of significant capital loss. Fundamental flaws, excessive valuation, or existential risks.",
        }
        return descriptions.get(recommendation, "No recommendation available.")

    def _assemble_report(self, sections: Dict, symbol: str, overall: Dict) -> str:
        """Assemble full markdown report."""
        parts = [
            f"# {symbol} - IPO Investment Research Report",
            "",
            f"**Date:** {datetime.utcnow().strftime('%B %d, %Y')}",
            f"**Analyst:** IPO Intelligence Agent",
            f"**Recommendation:** {overall.get('investment_strategy', 'WATCH')} | **Score:** {overall.get('overall_score', 0):.1f}/100",
            f"**Confidence:** {overall.get('confidence', 0):.0%} | **Risk:** {overall.get('risk_level', 'MODERATE')}",
            "",
            "---",
            "",
        ]

        # Order sections
        section_order = [
            "executive_summary",
            "ipo_overview",
            "company_background",
            "industry_analysis",
            "financial_analysis",
            "valuation_analysis",
            "risk_analysis",
            "management_assessment",
            "sentiment_analysis",
            "investment_thesis",
            "recommendation",
        ]

        for section in section_order:
            if section in sections:
                content = sections[section]
                if isinstance(content, dict):
                    content = content.get("full_thesis", str(content))
                parts.append(content)
                parts.append("\n---\n")

        return "\n".join(parts)

    def _extract_key_metrics(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
        overall: Dict,
    ) -> Dict[str, Any]:
        """Extract key metrics for structured output."""
        return {
            "overall_score": overall.get("overall_score", 0),
            "confidence": overall.get("confidence", 0),
            "recommendation": overall.get("investment_strategy", "WATCH"),
            "risk_level": overall.get("risk_level", "MODERATE"),
            "time_horizon": overall.get("time_horizon", "MEDIUM_TERM"),
            "financial_strength": overall.get("financial_strength_score", 0),
            "growth_potential": overall.get("growth_potential_score", 0),
            "market_opportunity": overall.get("market_opportunity_score", 0),
            "management_quality": overall.get("management_quality_score", 0),
            "risk_score": overall.get("risk_level_score", 50),
            "sentiment_score": sentiment.get("composite_score", 0),
            "sentiment_label": sentiment.get("composite_label", "NEUTRAL"),
            "tam": market.get("tam_analysis", {}).get("tam_usd", 0),
            "sam": market.get("sam_analysis", {}).get("sam_usd", 0),
            "som": market.get("som_analysis", {}).get("som_usd", 0),
            "key_risks_count": risk.get("high_priority_risks", 0),
            "red_flags_count": len(risk.get("red_flags", [])),
        }

    def _generate_financial_tables(
        self,
        financials: Dict,
        public_comps: List,
    ) -> List[Dict[str, Any]]:
        """Generate financial table configurations."""
        tables = []

        statements = financials.get("statements", [])
        if statements:
            # Income statement table
            income_data = []
            for s in statements[:8]:
                income_data.append({
                    "period": s.get("period", ""),
                    "revenue": s.get("revenue", 0),
                    "gross_profit": s.get("gross_profit", 0),
                    "operating_income": s.get("operating_income", 0),
                    "net_income": s.get("net_income", 0),
                    "ebitda": s.get("ebitda", 0),
                })
            tables.append({
                "title": "Income Statement History",
                "type": "income_statement",
                "data": income_data,
                "columns": ["period", "revenue", "gross_profit", "operating_income", "net_income", "ebitda"],
            })

            # Margins table
            margin_data = []
            for s in statements[:8]:
                margin_data.append({
                    "period": s.get("period", ""),
                    "gross_margin": s.get("gross_margin", 0),
                    "operating_margin": s.get("operating_margin", 0),
                    "net_margin": s.get("net_margin", 0),
                    "ebitda_margin": s.get("ebitda_margin", 0),
                    "fcf_margin": s.get("fcf_margin", 0),
                })
            tables.append({
                "title": "Margin Trends",
                "type": "margins",
                "data": margin_data,
                "columns": ["period", "gross_margin", "operating_margin", "net_margin", "ebitda_margin", "fcf_margin"],
            })

        # Peer comparison table
        if public_comps:
            comp_data = []
            for c in public_comps[:10]:
                comp_data.append({
                    "symbol": c.get("symbol", ""),
                    "name": c.get("name", ""),
                    "market_cap": c.get("market_cap", 0),
                    "ev_revenue": c.get("ev_revenue", 0),
                    "ev_ebitda": c.get("ev_ebitda", 0),
                    "pe_ratio": c.get("pe_ratio", 0),
                    "revenue_growth": c.get("revenue_growth", 0),
                    "profit_margin": c.get("profit_margin", 0),
                })
            tables.append({
                "title": "Public Comparable Companies",
                "type": "comps",
                "data": comp_data,
                "columns": ["symbol", "name", "market_cap", "ev_revenue", "ev_ebitda", "pe_ratio", "revenue_growth", "profit_margin"],
            })

        return tables

    def _generate_chart_configs(
        self,
        fundamental: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
    ) -> List[Dict[str, Any]]:
        """Generate chart configurations for frontend."""
        charts = []

        # Score breakdown chart
        overall = {}
        charts.append({
            "id": "score_breakdown",
            "type": "radar",
            "title": "Pillar Score Breakdown",
            "data": {
                "labels": ["Financial Strength", "Growth Potential", "Market Opportunity", "Management Quality", "Risk (Inverted)"],
                "datasets": [{
                    "label": "Scores",
                    "data": [
                        overall.get("financial_strength_score", 0),
                        overall.get("growth_potential_score", 0),
                        overall.get("market_opportunity_score", 0),
                        overall.get("management_quality_score", 0),
                        100 - overall.get("risk_level_score", 50),
                    ],
                }],
            },
        })

        # Sentiment breakdown
        breakdown = sentiment.get("source_breakdown", {})
        if breakdown:
            charts.append({
                "id": "sentiment_breakdown",
                "type": "bar",
                "title": "Sentiment by Source",
                "data": {
                    "labels": [k.title() for k in breakdown.keys()],
                    "datasets": [{
                        "label": "Sentiment Score",
                        "data": [v.get("score", 0) for v in breakdown.values()],
                        "backgroundColor": [
                            "rgba(34, 197, 94, 0.8)" if v.get("score", 0) > 0.2 else
                            "rgba(239, 68, 68, 0.8)" if v.get("score", 0) < -0.2 else
                            "rgba(107, 114, 128, 0.8)"
                            for v in breakdown.values()
                        ],
                    }],
                },
            })

        # Risk heatmap
        top_risks = risk.get("top_risks", [])[:10]
        if top_risks:
            charts.append({
                "id": "risk_heatmap",
                "type": "scatter",
                "title": "Risk Heatmap (Probability vs Impact)",
                "data": {
                    "datasets": [{
                        "label": "Risks",
                        "data": [
                            {
                                "x": r.get("probability", 0) * 100,
                                "y": r.get("impact", 0) * 100,
                                "r": r.get("risk_score", 10) / 2,
                                "label": r.get("factor", "Risk"),
                            }
                            for r in top_risks
                        ],
                    }],
                },
                "options": {
                    "scales": {
                        "x": {"title": {"display": True, "text": "Probability (%)"}},
                        "y": {"title": {"display": True, "text": "Impact (%)"}},
                    },
                },
            })

        # TAM/SAM/SOM waterfall
        tam = market.get("tam_analysis", {}).get("tam_usd", 0)
        sam = market.get("sam_analysis", {}).get("sam_usd", 0)
        som = market.get("som_analysis", {}).get("som_usd", 0)
        if tam > 0:
            charts.append({
                "id": "market_sizing",
                "type": "funnel",
                "title": "Market Sizing (TAM/SAM/SOM)",
                "data": {
                    "labels": ["TAM", "SAM", "SOM"],
                    "datasets": [{
                        "data": [tam, sam, som],
                        "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(34, 197, 94, 0.8)", "rgba(168, 85, 247, 0.8)"],
                    }],
                },
            })

        return charts

    def _compile_sources(
        self,
        financials: Dict,
        market: Dict,
        risk: Dict,
        sentiment: Dict,
        ipo_details: Dict,
    ) -> List[Dict[str, str]]:
        """Compile source references."""
        sources = []

        if financials.get("statements"):
            sources.append({
                "type": "Financial Statements",
                "description": f"Company filings ({len(financials['statements'])} periods)",
                "source": "SEC EDGAR / Company Filings",
            })

        if financials.get("public_comps"):
            sources.append({
                "type": "Peer Data",
                "description": f"Public comparable companies ({len(financials['public_comps'])} companies)",
                "source": "Yahoo Finance / Financial APIs",
            })

        if ipo_details.get("prospectus_url"):
            sources.append({
                "type": "IPO Prospectus",
                "description": "S-1 / F-1 Registration Statement",
                "source": ipo_details["prospectus_url"],
            })

        if market.get("industry_data"):
            sources.append({
                "type": "Industry Research",
                "description": "Market size, growth rates, competitive landscape",
                "source": "Industry Reports / Market Research",
            })

        if sentiment.get("source_breakdown"):
            active_sources = [k for k, v in sentiment["source_breakdown"].items() if v.get("count", 0) > 0]
            if active_sources:
                sources.append({
                    "type": "Sentiment Data",
                    "description": f"Sources: {', '.join(active_sources)}",
                    "source": "News APIs, Social Media, Analyst Reports",
                })

        sources.append({
            "type": "AI Analysis",
            "description": "Multi-agent analysis by IPO Intelligence Agent",
            "source": "Internal AI Models (Claude, GPT-4, Gemini)",
        })

        return sources

    def _get_standard_disclaimers(self) -> List[str]:
        """Get standard disclaimers."""
        return [
            "This report is for informational purposes only and does not constitute investment advice, "
            "an offer to sell, or a solicitation of an offer to buy any securities.",
            "The information contained herein is based on sources believed to be reliable but is not "
            "guaranteed as to accuracy or completeness.",
            "Past performance is not indicative of future results. Investment involves risk including "
            "possible loss of principal.",
            "The AI agents generating this analysis may make errors or have biases. Human review is "
            "recommended before making investment decisions.",
            "The analysts and agents involved in preparing this report may hold positions in the "
            "securities discussed.",
            "This report does not take into account individual investor circumstances, objectives, "
            "or risk tolerance.",
            "Forward-looking statements involve risks and uncertainties. Actual results may differ "
            "materially from projections.",
        ]

    def _generate_reasoning(self, overall: Dict) -> str:
        """Generate reasoning for the report generation."""
        return (
            f"Report generated with overall score {overall.get('overall_score', 0):.1f}/100, "
            f"recommendation {overall.get('investment_strategy', 'WATCH')}, "
            f"confidence {overall.get('confidence', 0):.0%}. "
            f"All major analysis pillars completed and synthesized."
        )

    def _collect_evidence(self, sections: Dict) -> List[str]:
        """Collect evidence from all sections."""
        evidence = []
        for section_name, content in sections.items():
            if isinstance(content, str) and len(content) > 100:
                evidence.append(f"{section_name}: {len(content)} chars of analysis")
        return evidence


def create_report_agent() -> ReportGenerationAgent:
    """Create report generation agent instance."""
    return ReportGenerationAgent()