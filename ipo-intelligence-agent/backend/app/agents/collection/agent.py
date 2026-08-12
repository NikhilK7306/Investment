"""Collection Agent - Collects comprehensive financial and alternative data for IPO analysis."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import yfinance as yf

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, DataSource
from app.domain.entities.entities import Company, FinancialStatement
from app.domain.value_objects.value_objects import IPODetails
from app.domain.value_objects.value_objects import Money, Percentage
from app.core.exceptions.base import AgentError


class CollectionAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that collects financial data, news, social sentiment, and alternative data."""

    def __init__(self):
        super().__init__(
            name=AgentName.COLLECTION,
            description="Collects comprehensive data from financial APIs, SEC filings, news, social media, and alternative sources",
            version="1.0.0",
            max_retries=3,
            timeout_seconds=300,
        )
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def system_prompt(self) -> str:
        return """You are a Data Collection Agent for IPO Intelligence.

Your task is to gather comprehensive data for IPO analysis from multiple sources:

1. FINANCIAL DATA
   - SEC EDGAR filings (S-1, F-1, 10-K, 10-Q, 8-K)
   - Financial statements (income, balance sheet, cash flow)
   - Key metrics and ratios
   - Historical financials (3-5 years)

2. MARKET DATA
   - Trading comparables (public peers)
   - Valuation multiples
   - Sector/industry benchmarks
   - Recent IPO performance

3. NEWS & MEDIA
   - Financial news (Bloomberg, Reuters, FT, WSJ)
   - Press releases
   - Analyst reports and ratings
   - Regulatory filings

4. SOCIAL & ALTERNATIVE DATA
   - Social media sentiment (Twitter/X, Reddit, StockTwits)
   - Web traffic and app analytics
   - Job postings and hiring trends
   - Credit card transaction data
   - Satellite/geospatial data

5. COMPANY INFORMATION
   - Management team and board
   - Business model and strategy
   - Competitive landscape
   - Cap table and ownership

Return structured, validated data with source attribution and confidence scores."""

    @property
    def available_tools(self) -> List[str]:
        return [
            "fetch_sec_filings",
            "fetch_financial_statements",
            "fetch_company_profile",
            "fetch_public_comps",
            "fetch_news_articles",
            "fetch_analyst_reports",
            "fetch_social_sentiment",
            "fetch_alternative_data",
            "fetch_ipo_details",
            "validate_financial_data",
        ]

    """Collection Agent - Collects comprehensive financial and alternative data for IPO analysis."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, DataSource
from app.domain.entities.entities import Company, FinancialStatement
from app.domain.value_objects.value_objects import IPODetails
from app.domain.value_objects.value_objects import Money, Percentage
from app.core.exceptions.base import AgentError
from app.infrastructure.external_services import get_provider_registry


class CollectionAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that collects financial data, news, social sentiment, and alternative data."""

    def __init__(self):
        super().__init__(
            name=AgentName.COLLECTION,
            description="Collects comprehensive data from financial APIs, SEC filings, news, social media, and alternative sources",
            version="2.0.0",
            max_retries=3,
            timeout_seconds=300,
        )
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def system_prompt(self) -> str:
        return """You are a Data Collection Agent for IPO Intelligence.

Your task is to gather comprehensive data for IPO analysis from multiple sources:

1. FINANCIAL DATA
   - SEC EDGAR filings (S-1, F-1, 10-K, 10-Q, 8-K)
   - Financial statements (income, balance sheet, cash flow)
   - Key metrics and ratios
   - Historical financials (3-5 years)

2. MARKET DATA
   - Trading comparables (public peers)
   - Valuation multiples
   - Sector/industry benchmarks
   - Recent IPO performance

3. NEWS & MEDIA
   - Financial news (Bloomberg, Reuters, FT, WSJ)
   - Press releases
   - Analyst reports and ratings
   - Regulatory filings

4. SOCIAL & ALTERNATIVE DATA
   - Social media sentiment (Twitter/X, Reddit, StockTwits)
   - Web traffic and app analytics
   - Job postings and hiring trends
   - Credit card transaction data
   - Satellite/geospatial data

5. COMPANY INFORMATION
   - Management team and board
   - Business model and strategy
   - Competitive landscape
   - Cap table and ownership

Return structured, validated data with source attribution and confidence scores.
All data must include source provenance (source, source_reference, retrieved_at)."""

    @property
    def available_tools(self) -> List[str]:
        return [
            "fetch_sec_filings",
            "fetch_financial_statements",
            "fetch_company_profile",
            "fetch_public_comps",
            "fetch_news_articles",
            "fetch_analyst_reports",
            "fetch_social_sentiment",
            "fetch_alternative_data",
            "fetch_ipo_details",
            "validate_financial_data",
        ]

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute data collection using provider registry."""
        start_time = datetime.utcnow()

        try:
            symbol = context.ipo_symbol
            ipo_details = input_data.get("ipo_details", {})
            depth = context.depth

            # Initialize HTTP client
            await self._init_http_client()

            # Get provider registry
            registry = get_provider_registry()

            # Collect data in parallel
            tasks = [
                self._collect_financial_data(symbol, ipo_details),
                self._collect_company_profile(symbol, ipo_details),
                self._collect_public_comps(symbol, ipo_details),
                self._collect_news_and_media(symbol, ipo_details, registry),
                self._collect_social_sentiment(symbol, ipo_details, registry),
                self._collect_alternative_data(symbol, registry),
                self._collect_ipo_specific_data(symbol, ipo_details),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            financial_data = results[0] if not isinstance(results[0], Exception) else {}
            company_profile = results[1] if not isinstance(results[1], Exception) else {}
            public_comps = results[2] if not isinstance(results[2], Exception) else []
            news_media = results[3] if not isinstance(results[3], Exception) else {}
            social_sentiment = results[4] if not isinstance(results[4], Exception) else {}
            alternative_data = results[5] if not isinstance(results[5], Exception) else {}
            ipo_data = results[6] if not isinstance(results[6], Exception) else {}

            # Validate and score data quality
            quality_score = self._assess_data_quality(
                financial_data, company_profile, public_comps, news_media
            )

            result_data = {
                "financials": financial_data,
                "company_profile": company_profile,
                "public_comps": public_comps,
                "news": news_media.get("news", []),
                "analyst_reports": news_media.get("analyst_reports", []),
                "social_media": social_sentiment,
                "alternative_data": alternative_data,
                "ipo_details": ipo_data,
                "data_quality_score": quality_score,
                "sources_used": self._get_sources_used(results),
                "collection_timestamp": datetime.utcnow().isoformat(),
            }

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                confidence=quality_score,
                reasoning=f"Collected data from {len(self._get_sources_used(results))} sources with quality score {quality_score:.0%}",
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

    async def _init_http_client(self) -> None:
        """Initialize HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"User-Agent": "IPO Intelligence Agent/1.0"},
            )

    async def _collect_financial_data(
        self,
        symbol: str,
        ipo_details: Dict,
    ) -> Dict[str, Any]:
        """Collect financial statements and metrics using provider fallback chain."""
        financials = {"statements": [], "metrics": {}, "ratios": {}, "sources": [], "errors": []}
        
        # Get financial providers from registry (fallback chain)
        registry = get_provider_registry()
        financial_providers = registry.get_financial_providers()
        
        # Try each financial provider in order
        for provider in financial_providers:
            if not provider.config.enabled:
                continue
                
            try:
                # First try to fetch financials for listed companies
                result = await provider.fetch_financials(symbol, periods=8)
                
                if result.success and result.data:
                    statements = result.data.get("statements", [])
                    if statements:
                        financials["statements"] = statements
                        financials["metrics"] = self._calculate_metrics_from_statements(statements)
                        financials["ratios"] = self._calculate_ratios_from_statements(statements)
                        financials["sources"].append({
                            "provider": result.source,
                            "reference": result.source_reference,
                            "retrieved_at": result.retrieved_at.isoformat() if hasattr(result.retrieved_at, 'isoformat') else str(result.retrieved_at),
                            "periods": len(statements),
                        })
                        break  # Success - stop fallback chain
                
            except Exception as e:
                financials["errors"].append({
                    "provider": provider.name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                })
                continue
        
        # If no financial data found and it's a pre-IPO company, try DRHP extraction
        if not financials["statements"] and ipo_details.get("prospectus_url"):
            try:
                drhp_provider = next((p for p in financial_providers if p.name == "drhp_document"), None)
                if drhp_provider:
                    company_name = ipo_details.get("company_name", symbol)
                    drhp_result = await drhp_provider.fetch_drhp_financials(
                        symbol=symbol,
                        company_name=company_name,
                        ipo_details=ipo_details,
                    )
                    if drhp_result.success and drhp_result.data:
                        statements = drhp_result.data.get("statements", [])
                        if statements:
                            financials["statements"] = statements
                            financials["metrics"] = self._calculate_metrics_from_statements(statements)
                            financials["ratios"] = self._calculate_ratios_from_statements(statements)
                            financials["sources"].append({
                                "provider": drhp_result.source,
                                "reference": drhp_result.source_reference,
                                "retrieved_at": drhp_result.retrieved_at.isoformat() if hasattr(drhp_result.retrieved_at, 'isoformat') else str(drhp_result.retrieved_at),
                                "periods": len(statements),
                                "extraction_method": drhp_result.data.get("extraction_method", "pdf_parsing"),
                            })
            except Exception as e:
                financials["errors"].append({
                    "provider": "drhp_document",
                    "error": f"DRHP extraction failed: {str(e)}",
                    "error_type": type(e).__name__,
                })
        
        # Also try to fetch company profile from financial providers
        for provider in financial_providers:
            if not provider.config.enabled or provider.name == "drhp_document":
                continue
            try:
                profile_result = await provider.fetch_company_profile(symbol)
                if profile_result.success and profile_result.data:
                    financials["company_profile"] = profile_result.data
                    financials["sources"].append({
                        "provider": profile_result.source,
                        "reference": profile_result.source_reference,
                        "type": "company_profile",
                    })
                    break
            except Exception:
                continue
        
        return financials

    def _calculate_metrics_from_statements(self, statements: List[Dict]) -> Dict[str, Any]:
        """Calculate key financial metrics from statements."""
        if not statements:
            return {}
        
        latest = statements[0]
        metrics = {}
        
        revenue = latest.get("revenue")
        gross_profit = latest.get("gross_profit")
        operating_income = latest.get("operating_income")
        net_income = latest.get("net_income")
        ebitda = latest.get("ebitda")
        total_assets = latest.get("total_assets")
        total_equity = latest.get("total_equity")
        cash = latest.get("cash_and_equivalents")
        total_debt = latest.get("total_debt")
        fcf = latest.get("free_cash_flow")
        
        if revenue and revenue > 0:
            if gross_profit:
                metrics["gross_margin"] = gross_profit / revenue
            if operating_income:
                metrics["operating_margin"] = operating_income / revenue
            if net_income:
                metrics["net_margin"] = net_income / revenue
            if ebitda:
                metrics["ebitda_margin"] = ebitda / revenue
            if fcf:
                metrics["fcf_margin"] = fcf / revenue
        
        if total_assets and total_assets > 0:
            if net_income:
                metrics["roa"] = net_income / total_assets
        
        if total_equity and total_equity > 0:
            if net_income:
                metrics["roe"] = net_income / total_equity
            if total_debt:
                metrics["debt_to_equity"] = total_debt / total_equity
        
        if ebitda and total_debt:
            metrics["debt_to_ebitda"] = total_debt / ebitda
        
        if fcf and net_income and net_income > 0:
            metrics["fcf_conversion"] = fcf / net_income
        
        # Growth metrics (YoY) - need at least 2 periods
        if len(statements) >= 2:
            prev = statements[1]
            prev_revenue = prev.get("revenue")
            if revenue and prev_revenue and prev_revenue > 0:
                metrics["revenue_growth_yoy"] = (revenue - prev_revenue) / prev_revenue
        
        return metrics

    def _calculate_ratios_from_statements(self, statements: List[Dict]) -> Dict[str, float]:
        """Calculate financial ratios from statements."""
        if not statements:
            return {}
        
        latest = statements[0]
        ratios = {}
        
        current_assets = latest.get("total_current_assets")
        current_liabilities = latest.get("total_current_liabilities")
        inventory = latest.get("inventory")
        ebitda = latest.get("ebitda")
        interest_expense = latest.get("interest_expense")
        
        if current_assets and current_liabilities and current_liabilities > 0:
            ratios["current_ratio"] = current_assets / current_liabilities
            if inventory:
                ratios["quick_ratio"] = (current_assets - inventory) / current_liabilities
        
        # Interest coverage
        if ebitda and interest_expense and interest_expense > 0:
            ratios["interest_coverage"] = ebitda / interest_expense
        
        return ratios

    async def _fetch_sec_filings(self, symbol: str, company_name: str = "") -> List[Dict]:
        """Fetch recent SEC filings for pre-IPO companies from EDGAR."""
        headers = {
            "User-Agent": "IPO Intelligence Research dev@example.com",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                cik = None
                try:
                    tickers_resp = await client.get(
                        "https://www.sec.gov/files/company_tickers.json", headers=headers
                    )
                    if tickers_resp.status_code == 200:
                        for entry in tickers_resp.json().values():
                            if str(entry.get("ticker", "")).upper() == symbol.upper():
                                cik = entry.get("cik_str")
                                break
                except Exception:
                    pass
                if cik:
                    return await self._sec_filings_by_cik(client, headers, cik)
                if company_name:
                    return await self._sec_filings_by_name(client, headers, company_name)
                return []
        except Exception:
            return []

    async def _sec_filings_by_cik(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        cik: int,
    ) -> List[Dict]:
        sub_resp = await client.get(
            f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json",
            headers=headers,
        )
        if sub_resp.status_code != 200:
            return []
        data = sub_resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", []) or []
        accessions = recent.get("accessionNumber", []) or []
        filing_dates = recent.get("filingDate", []) or []
        primary_docs = recent.get("primaryDocument", []) or []
        filings = []
        for i, form in enumerate(forms):
            if form not in ("S-1", "S-1A", "F-1", "F-1A", "10-K", "10-Q", "8-K"):
                continue
            accession = accessions[i] if i < len(accessions) else ""
            acc_no = accession.replace("-", "")
            primary = primary_docs[i] if i < len(primary_docs) else ""
            filings.append({
                "filing_type": form,
                "date": filing_dates[i] if i < len(filing_dates) else "",
                "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{primary}",
            })
            if len(filings) >= 10:
                break
        return filings

    async def _sec_filings_by_name(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        company_name: str,
    ) -> List[Dict]:
        """Search EDGAR full-text index for the company's IPO filings by name."""
        response = await client.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={
                "q": f'"{company_name}"',
                "forms": "S-1,F-1,10-K,10-Q,8-K",
                "dateRange": "y",
            },
            headers=headers,
        )
        if response.status_code != 200:
            return []
        hits = response.json().get("hits", {}).get("hits", []) or []
        allowed = ("S-1", "F-1", "10-K", "10-Q", "8-K")
        filings = []
        seen = set()
        for hit in hits:
            src = hit.get("_source", {}) or {}
            display = src.get("display_names") or []
            if not display or company_name.lower() not in str(display[0]).lower():
                continue
            base_form = str(src.get("form", "")).split("/")[0]
            if base_form not in allowed:
                continue
            filing_date = src.get("file_date", "")
            dedupe_key = (base_form, filing_date)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            ciks = src.get("ciks") or []
            adsh = str(src.get("adsh", "")).replace("-", "")
            url = (
                f"https://www.sec.gov/Archives/edgar/data/{ciks[0]}/{adsh}/"
                if ciks and adsh else ""
            )
            filings.append({
                "filing_type": base_form,
                "date": src.get("file_date", ""),
                "url": url,
            })
            if len(filings) >= 10:
                break
        return filings

    async def _collect_company_profile(
        self,
        symbol: str,
        ipo_details: Dict,
    ) -> Dict[str, Any]:
        """Collect company profile information."""
        profile = ipo_details.copy()
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if info:
                profile.update({
                    "legal_name": info.get("longName", ""),
                    "description": info.get("longBusinessSummary", ""),
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "website": info.get("website", ""),
                    "employees": info.get("fullTimeEmployees"),
                    "headquarters": f"{info.get('city', '')}, {info.get('state', '')}, {info.get('country', '')}".strip(", "),
                    "ceo": info.get("ceo", ""),
                    "market_cap": info.get("marketCap"),
                    "enterprise_value": info.get("enterpriseValue"),
                })
        except Exception:
            pass

        return profile

    async def _collect_public_comps(
        self,
        symbol: str,
        ipo_details: Dict,
    ) -> List[Dict[str, Any]]:
        """Collect public comparable companies."""
        # In production, this would query a financial database
        # For now, return placeholder based on sector
        sector = ipo_details.get("sector", "technology")
        
        comps_by_sector = {
            "technology": ["MSFT", "GOOGL", "AMZN", "META", "NVDA"],
            "healthcare": ["JNJ", "PFE", "MRK", "ABBV", "LLY"],
            "financials": ["JPM", "BAC", "WFC", "GS", "MS"],
            "consumer": ["AAPL", "TSLA", "NKE", "SBUX", "MCD"],
        }
        
        tickers = comps_by_sector.get(sector.lower(), comps_by_sector["technology"])
        comps = []
        
        for ticker in tickers[:5]:
            try:
                t = yf.Ticker(ticker)
                info = t.info
                if info:
                    comps.append({
                        "symbol": ticker,
                        "name": info.get("longName", ticker),
                        "market_cap": info.get("marketCap"),
                        "ev_revenue": info.get("enterpriseToRevenue"),
                        "ev_ebitda": info.get("enterpriseToEbitda"),
                        "pe_ratio": info.get("trailingPE"),
                        "revenue_growth": info.get("revenueGrowth"),
                        "profit_margin": info.get("profitMargins"),
                    })
            except Exception:
                continue

        return comps

    async def _collect_news_and_media(
        self,
        symbol: str,
        ipo_details: Dict,
        registry,
    ) -> Dict[str, Any]:
        """Collect news articles and analyst reports using news providers."""
        news = []
        analyst_reports = []
        
        # Get news providers
        news_providers = registry.get_news_providers()
        
        for provider in news_providers:
            if not provider.config.enabled:
                continue
            
            try:
                result = await provider.fetch_news(
                    query=symbol,
                    limit=20,
                    from_date=datetime.utcnow() - timedelta(days=30),
                )
                
                if result.success and result.data:
                    # Add source metadata to each article
                    for article in result.data:
                        article["_source"] = result.source
                        article["_source_reference"] = result.source_reference
                        article["_retrieved_at"] = result.retrieved_at.isoformat()
                    news.extend(result.data)
                    
            except Exception as e:
                # Log but continue with other providers
                pass
        
        return {
            "news": news,
            "analyst_reports": analyst_reports,
        }

    async def _collect_social_sentiment(
        self,
        symbol: str,
        ipo_details: Dict,
        registry,
    ) -> Dict[str, Any]:
        """Collect social media sentiment data using social providers."""
        # Note: Social providers are not in the news provider registry
        # They would be in a separate social provider registry
        # For now, return empty structure - social providers need separate integration
        
        social_data = {
            "twitter": [],
            "reddit": [],
            "stocktwits": [],
            "aggregated_score": 0.0,
        }
        
        # Try to get social data from news providers that include social
        # (e.g., Alpha Vantage includes some social sentiment)
        news_providers = registry.get_news_providers()
        
        for provider in news_providers:
            if not provider.config.enabled:
                continue
            
            if provider.name == "alphavantage_news":
                try:
                    result = await provider.fetch_news(
                        query=symbol,
                        limit=50,
                        from_date=datetime.utcnow() - timedelta(days=7),
                    )
                    
                    if result.success and result.data:
                        # Extract sentiment from Alpha Vantage data
                        for article in result.data:
                            sentiment_score = article.get("sentiment_score")
                            if sentiment_score is not None:
                                social_data["aggregated_score"] += sentiment_score
                        
                        if social_data["aggregated_score"] != 0:
                            social_data["aggregated_score"] /= len(result.data)
                            
                except Exception:
                    pass
        
        return social_data

    async def _collect_alternative_data(
        self,
        symbol: str,
        registry,
    ) -> Dict[str, Any]:
        """Collect alternative data signals."""
        # In production, integrate with alternative data providers
        # For now, return structured placeholder with source tracking
        return {
            "web_traffic": [],
            "app_downloads": [],
            "job_postings": [],
            "credit_card_spend": [],
            "employee_reviews": [],
            "_sources": [],
        }

    async def _collect_ipo_specific_data(
        self,
        symbol: str,
        ipo_details: Dict,
    ) -> Dict[str, Any]:
        """Collect IPO-specific details."""
        return {
            "expected_date": ipo_details.get("expected_date"),
            "price_range": ipo_details.get("price_range"),
            "shares_offered": ipo_details.get("shares_offered"),
            "underwriters": ipo_details.get("underwriters", []),
            "use_of_proceeds": ipo_details.get("use_of_proceeds", ""),
            "lockup_period": ipo_details.get("lockup_period_days"),
            "prospectus_url": ipo_details.get("prospectus_url", ""),
        }

    def _assess_data_quality(
        self,
        financials: Dict,
        profile: Dict,
        comps: List,
        news: Dict,
    ) -> float:
        """Assess overall data quality."""
        score = 0.0
        
        # Financial data quality
        if financials.get("statements"):
            score += 0.3
            # Bonus for multiple periods
            if len(financials["statements"]) >= 4:
                score += 0.1
        if financials.get("metrics"):
            score += 0.1
        if financials.get("company_profile"):
            score += 0.1
        
        # Profile quality
        if profile.get("legal_name"):
            score += 0.15
        
        # Comps quality
        if comps:
            score += 0.15
        
        # News quality
        if news.get("news"):
            score += 0.1
        if news.get("analyst_reports"):
            score += 0.1
        
        return min(1.0, score)

    def _get_sources_used(self, results: List) -> List[str]:
        """Get list of sources used."""
        sources = []
        
        # Financial sources from results
        for r in results:
            if isinstance(r, dict):
                # Financial data sources
                if "financials" in r and r["financials"].get("sources"):
                    for src in r["financials"]["sources"]:
                        if src.get("provider") and src["provider"] not in sources:
                            sources.append(src["provider"])
                # News sources
                if "news" in r:
                    for article in r.get("news", []):
                        if "_source" in article and article["_source"] not in sources:
                            sources.append(article["_source"])
                # SEC filings
                if r.get("sec_filings"):
                    sources.append("sec_edgar")
        
        return sources

    def _collect_evidence(self, result_data: Dict) -> List[str]:
        """Collect evidence for the result."""
        evidence = []
        
        if result_data.get("financials", {}).get("statements"):
            evidence.append(f"Financial statements: {len(result_data['financials']['statements'])} periods")
        if result_data.get("public_comps"):
            evidence.append(f"Public comps: {len(result_data['public_comps'])} companies")
        if result_data.get("news"):
            evidence.append(f"News articles: {len(result_data['news'])}")
        
        return evidence


# Factory function
def create_collection_agent() -> CollectionAgent:
    """Create collection agent instance."""
    return CollectionAgent()