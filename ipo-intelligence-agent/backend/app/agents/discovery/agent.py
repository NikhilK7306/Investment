"""Discovery Agent - finds upcoming IPOs from multiple sources."""

import asyncio
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from app.agents.base.agent import AgentContext, AgentResult, BaseAgent
from app.domain.enums.enums import AgentName, AgentStatus, Exchange, IPOStatus, Sector, Industry
from app.domain.value_objects.value_objects import IPODetails, PriceRange
from app.domain.value_objects.value_objects import Money, Percentage
from app.core.exceptions.base import AgentError


class DiscoveryAgent(BaseAgent[Dict[str, Any], List[IPODetails]]):
    """Agent that discovers upcoming IPOs from multiple sources."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.DISCOVERY,
            description="Discovers upcoming IPOs from exchanges, SEC filings, and financial news",
            version="1.0.0",
            max_retries=3,
            timeout_seconds=120,
        )
        self._sources = {
            "nasdaq": "https://www.nasdaq.com/market-activity/ipos",
            "nyse": "https://www.nyse.com/ipo-center",
            "sec": "https://www.sec.gov/cgi-bin/browse-edgar",
            "ipowatch": "https://www.ipowatch.com/upcoming-ipos/",
            "renaissance": "https://www.renaissancecapital.com/ipo-calendar",
            "investorgain": "https://www.investorgain.com/report/ipo-gmp-live/331/all/",
        }
        self._seen_symbols: Set[str] = set()
    
    @property
    def system_prompt(self) -> str:
        return """You are an IPO Discovery Agent. Your job is to identify and extract information about upcoming IPOs from various data sources.

You have access to web scraping tools and financial APIs. When analyzing sources, look for:
1. Company name and ticker symbol
2. Exchange (NASDAQ, NYSE, etc.)
3. Expected IPO date
4. Price range (if available)
5. Shares offered
6. Industry/sector
7. Underwriters
8. Use of proceeds

Return structured data for each IPO found. Be thorough but avoid duplicates."""
    
    @property
    def available_tools(self) -> List[str]:
        return [
            "fetch_nasdaq_ipos",
            "fetch_nyse_ipos",
            "fetch_sec_filings",
            "fetch_renaissance_calendar",
            "fetch_ipowatch",
            "fetch_investorgain_ipos",
            "validate_ipo_data",
            "check_duplicate",
        ]
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[List[IPODetails]]:
        """Execute IPO discovery."""
        start_time = datetime.utcnow()
        discovered_ipos = []
        errors = []
        
        # Get configuration
        lookahead_days = input_data.get("lookahead_days", 90)
        sources = input_data.get("sources", ["nasdaq", "nyse", "sec", "renaissance"])
        min_market_cap = input_data.get("min_market_cap", 0)
        
        # Run discovery for each source
        source_tasks = []
        if "nasdaq" in sources:
            source_tasks.append(self._fetch_nasdaq_ipos(lookahead_days))
        if "nyse" in sources:
            source_tasks.append(self._fetch_nyse_ipos(lookahead_days))
        if "sec" in sources:
            source_tasks.append(self._fetch_sec_filings(lookahead_days))
        if "renaissance" in sources:
            source_tasks.append(self._fetch_renaissance_calendar(lookahead_days))
        if "investorgain" in sources:
            source_tasks.append(self._fetch_investorgain_ipos())
        
        # Execute in parallel
        results = await asyncio.gather(*source_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            source_name = sources[i]
            if isinstance(result, Exception):
                errors.append(f"{source_name}: {str(result)}")
            elif isinstance(result, list):
                discovered_ipos.extend(result)
        
        # Deduplicate
        unique_ipos = self._deduplicate_ipos(discovered_ipos)
        
        # Filter by minimum market cap if specified
        if min_market_cap > 0:
            unique_ipos = [
                ipo for ipo in unique_ipos
                if ipo.valuation and ipo.valuation.equity_value.amount >= min_market_cap
            ]
        
        # Enrich with additional data
        enriched_ipos = await self._enrich_ipos(unique_ipos)
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED if not errors else AgentStatus.PARTIAL,
            data=enriched_ipos,
            error="; ".join(errors) if errors else None,
            confidence=0.9 if not errors else 0.7,
            reasoning=f"Discovered {len(enriched_ipos)} unique IPOs from {len(sources)} sources",
            evidence=[f"Source: {s}" for s in sources] + errors,
            metadata={
                "sources_checked": sources,
                "total_found": len(discovered_ipos),
                "after_dedup": len(unique_ipos),
                "after_filter": len(enriched_ipos),
                "errors": errors,
            },
            duration_ms=duration_ms,
        )
    
    async def _fetch_nasdaq_ipos(self, lookahead_days: int) -> List[IPODetails]:
        """Fetch IPOs from NASDAQ."""
        ipos = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.nasdaq.com/api/ipo/calendar",
                    params={"limit": 100},
                    headers={"User-Agent": "IPO Intelligence Agent/1.0"},
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("data", {}).get("upcoming", []):
                        ipo = self._parse_nasdaq_item(item)
                        if ipo:
                            ipos.append(ipo)
        except Exception as e:
            raise AgentError(f"NASDAQ fetch failed: {e}", self.name.value)
        return ipos
    
    def _parse_nasdaq_item(self, item: Dict[str, Any]) -> Optional[IPODetails]:
        """Parse NASDAQ IPO item."""
        try:
            symbol = item.get("symbol", "").upper()
            if not symbol or symbol in self._seen_symbols:
                return None
            
            self._seen_symbols.add(symbol)
            
            expected_date = None
            if item.get("expectedDate"):
                expected_date = datetime.fromisoformat(item["expectedDate"].replace("Z", "+00:00"))
            
            price_range = None
            if item.get("priceRange"):
                parts = item["priceRange"].split(" - ")
                if len(parts) == 2:
                    low = Money.from_string(parts[0].strip())
                    high = Money.from_string(parts[1].strip())
                    price_range = PriceRange(low=low, high=high)
            
            return IPODetails(
                symbol=symbol,
                company_name=item.get("companyName", ""),
                exchange=Exchange.NASDAQ,
                expected_date=expected_date,
                status=IPOStatus.FILED.value,
                shares_offered=item.get("sharesOffered"),
                price_range=price_range,
                underwriters=item.get("underwriters", []),
                sector=self._map_sector(item.get("sector", "")),
                industry=self._map_industry(item.get("industry", "")),
            )
        except Exception:
            return None
    
    async def _fetch_nyse_ipos(self, lookahead_days: int) -> List[IPODetails]:
        """Fetch IPOs from NYSE."""
        ipos = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.nyse.com/api/ipo/calendar",
                    headers={"User-Agent": "IPO Intelligence Agent/1.0"},
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("upcoming", []):
                        ipo = self._parse_nyse_item(item)
                        if ipo:
                            ipos.append(ipo)
        except Exception as e:
            raise AgentError(f"NYSE fetch failed: {e}", self.name.value)
        return ipos
    
    def _parse_nyse_item(self, item: Dict[str, Any]) -> Optional[IPODetails]:
        """Parse NYSE IPO item."""
        try:
            symbol = item.get("symbol", "").upper()
            if not symbol or symbol in self._seen_symbols:
                return None
            
            self._seen_symbols.add(symbol)
            
            expected_date = None
            if item.get("expectedDate"):
                expected_date = datetime.fromisoformat(item["expectedDate"])
            
            price_range = None
            if item.get("priceLow") and item.get("priceHigh"):
                low = Money(amount=item["priceLow"], currency="USD")
                high = Money(amount=item["priceHigh"], currency="USD")
                price_range = PriceRange(low=low, high=high)
            
            return IPODetails(
                symbol=symbol,
                company_name=item.get("companyName", ""),
                exchange=Exchange.NYSE,
                expected_date=expected_date,
                status=IPOStatus.FILED.value,
                shares_offered=item.get("sharesOffered"),
                price_range=price_range,
                underwriters=item.get("underwriters", []),
                sector=self._map_sector(item.get("sector", "")),
                industry=self._map_industry(item.get("industry", "")),
            )
        except Exception:
            return None
    
    async def _fetch_sec_filings(self, lookahead_days: int) -> List[IPODetails]:
        """Fetch IPOs from SEC EDGAR filings (S-1, F-1)."""
        ipos = []
        try:
            # This would use SEC EDGAR API or scraping
            # For now, return empty list - would be implemented with sec-edgar-downloader
            pass
        except Exception as e:
            raise AgentError(f"SEC fetch failed: {e}", self.name.value)
        return ipos
    
    async def _fetch_renaissance_calendar(self, lookahead_days: int) -> List[IPODetails]:
        """Fetch from Renaissance Capital IPO calendar."""
        ipos = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.renaissancecapital.com/ipo-calendar",
                    headers={"User-Agent": "IPO Intelligence Agent/1.0"},
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Parse the calendar table
                    # This would need actual HTML parsing based on their structure
                    pass
        except Exception as e:
            raise AgentError(f"Renaissance fetch failed: {e}", self.name.value)
        return ipos
    
    async def _fetch_investorgain_ipos(self) -> List[IPODetails]:
        """Fetch Indian IPO GMP data from investorgain.com."""
        ipos = []
        now = datetime.utcnow()
        fy = f"{now.year}-{str(now.year + 1)[-2:]}" if now.month >= 4 else f"{now.year - 1}-{str(now.year)[-2:]}"
        hosts = ["webnodejs.investorgain.com", "alphanodejs.investorgain.com"]

        last_error = None
        for host in hosts:
            url = (
                f"https://{host}/cloud/v2/report/data-read/331/1/"
                f"{now.month}/{now.year}/{fy}/0/all?search="
            )
            try:
                async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                    response = await client.get(url, headers={"User-Agent": "IPO Intelligence Agent/1.0"})
                    if response.status_code != 200:
                        last_error = AgentError(f"investorgain {host} returned {response.status_code}")
                        continue
                    data = response.json()
                    if data.get("msg") != 1:
                        last_error = AgentError(f"investorgain {host} returned unexpected payload")
                        continue
                    for item in data.get("reportTableData", []):
                        ipo = self._parse_investorgain_item(item)
                        if ipo:
                            ipos.append(ipo)
                    return ipos
            except Exception as e:
                last_error = AgentError(f"investorgain {host} fetch failed: {e}")

        raise AgentError(f"investorgain fetch failed: {last_error}", self.name.value)

    def _parse_investorgain_item(self, item: Dict[str, Any]) -> Optional[IPODetails]:
        """Parse a single investorgain GMP table row."""
        try:
            name = (item.get("~ipo_name") or "").strip()
            if not name:
                return None

            symbol = self._to_symbol(name)
            if not symbol or symbol in self._seen_symbols:
                return None
            self._seen_symbols.add(symbol)

            name_html = item.get("Name", "")
            category = (item.get("~IPO_Category") or "").upper()

            exchange = Exchange.NSE
            if "BSE" in name_html.upper():
                exchange = Exchange.BSE

            today = datetime.utcnow().date()
            expected_date = self._parse_date(item.get("~Srt_Open"))
            close_date = self._parse_date(item.get("~Srt_Close"))
            listing_date = self._parse_date(item.get("~Str_Listing"))

            status = IPOStatus.ANNOUNCED
            if listing_date and listing_date.date() < today:
                status = IPOStatus.LISTED
            elif expected_date:
                status = IPOStatus.FILED

            price_range = None
            offer_price = None
            price_raw = (item.get("Price (₹)") or "").strip()
            if price_raw:
                parts = [p.strip() for p in price_raw.split("-")]
                try:
                    low = Decimal(parts[0].replace(",", ""))
                    high = Decimal(parts[1].replace(",", "")) if len(parts) > 1 else low
                    price_range = PriceRange(low=Money(low, "INR"), high=Money(high, "INR"))
                    if len(parts) == 1:
                        offer_price = Money(low, "INR")
                except Exception:
                    price_range = None

            expected_raise = self._parse_size(item.get("IPO Size"))

            return IPODetails(
                symbol=symbol,
                company_name=name,
                exchange=exchange,
                expected_date=expected_date,
                listed_date=listing_date,
                status=status.value,
                price_range=price_range,
                offer_price=offer_price,
                expected_raise=expected_raise,
                sector=Sector.UNCLASSIFIED,
                industry=Industry.OTHER,
            )
        except Exception:
            return None

    @staticmethod
    def _to_symbol(name: str) -> str:
        """Convert an IPO name to an uppercase alphanumeric symbol."""
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        if len(cleaned) > 20:
            cleaned = cleaned[:20]
        return cleaned

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """Parse an ISO date string (e.g. 2026-08-12)."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_size(value: Any) -> Optional[Money]:
        """Parse Indian IPO size strings like '₹1617.48 Cr' or '₹42.84 L'."""
        if not value:
            return None
        text = str(value)
        match = re.search(r"([\d,]+(?:\.\d+)?)\s*(Cr|Crore|L|Lakh|K)?", text, re.IGNORECASE)
        if not match:
            return None
        try:
            number = Decimal(match.group(1).replace(",", ""))
            unit = (match.group(2) or "").upper()
            multiplier = {"CR": Decimal("10000000"), "CRORE": Decimal("10000000"),
                          "L": Decimal("100000"), "LAKH": Decimal("100000"),
                          "K": Decimal("1000")}.get(unit, Decimal("1"))
            return Money(number * multiplier, "INR")
        except Exception:
            return None

    async def _enrich_ipos(self, ipos: List[IPODetails]) -> List[IPODetails]:
        """Enrich IPOs with additional data."""
        # In production, this would fetch additional details
        # like company profiles, financials, etc.
        return ipos
    
    def _deduplicate_ipos(self, ipos: List[IPODetails]) -> List[IPODetails]:
        """Remove duplicate IPOs based on symbol."""
        seen = set()
        unique = []
        for ipo in ipos:
            if ipo.symbol not in seen:
                seen.add(ipo.symbol)
                unique.append(ipo)
        return unique
    
    def _map_sector(self, sector: str) -> Sector:
        """Map sector string to enum."""
        sector_lower = sector.lower()
        mapping = {
            "technology": Sector.INFORMATION_TECHNOLOGY,
            "healthcare": Sector.HEALTH_CARE,
            "financial": Sector.FINANCIALS,
            "consumer": Sector.CONSUMER_DISCRETIONARY,
            "industrial": Sector.INDUSTRIALS,
            "energy": Sector.ENERGY,
            "materials": Sector.MATERIALS,
            "utilities": Sector.UTILITIES,
            "real estate": Sector.REAL_ESTATE,
            "communication": Sector.COMMUNICATION_SERVICES,
        }
        for key, value in mapping.items():
            if key in sector_lower:
                return value
        return Sector.UNCLASSIFIED
    
    def _map_industry(self, industry: str) -> Industry:
        """Map industry string to enum."""
        industry_lower = industry.lower()
        mapping = {
            "software": Industry.SOFTWARE,
            "biotech": Industry.BIOTECH,
            "pharmaceutical": Industry.PHARMACEUTICALS,
            "fintech": Industry.FINTECH,
            "semiconductor": Industry.SEMICONDUCTORS,
            "ai": Industry.AI_ML,
            "cybersecurity": Industry.CYBERSECURITY,
        }
        for key, value in mapping.items():
            if key in industry_lower:
                return value
        return Industry.OTHER