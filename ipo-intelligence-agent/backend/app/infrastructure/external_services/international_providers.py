"""International IPO data providers (NASDAQ, NYSE, SEC EDGAR)."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.domain.enums.enums import Exchange, IPOStatus, Sector, Industry
from app.domain.value_objects.value_objects import IPODetails, Money, PriceRange
from app.infrastructure.external_services.providers import (
    IPODataProvider,
    ProviderConfig,
    ProviderResult,
)


class NASDAQProvider(IPODataProvider):
    """Provider for NASDAQ IPO calendar data."""

    def __init__(self):
        config = ProviderConfig(
            name="nasdaq",
            base_url="https://api.nasdaq.com",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=60,
            headers={
                "User-Agent": "IPO Intelligence Agent/1.0",
                "Accept": "application/json",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/api/ipo/calendar", params={"limit": 1}, timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"NASDAQ API returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        """Fetch upcoming IPOs from NASDAQ."""
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/ipo/calendar",
                params={"limit": 200},
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"NASDAQ API returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="nasdaq.com",
                )
            
            data = response.json()
            ipos = self._parse_nasdaq_data(data)
            
            # Filter by exchange if specified
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="nasdaq.com",
                source_reference="https://api.nasdaq.com/api/ipo/calendar",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="nasdaq.com",
            )

    def _parse_nasdaq_data(self, data: Dict[str, Any]) -> List[IPODetails]:
        """Parse NASDAQ IPO calendar API response."""
        ipos = []
        sections = data.get("data", {})
        
        for section_name in ("filed", "upcoming", "priced", "withdrawn"):
            section = sections.get(section_name)
            if not isinstance(section, dict):
                continue
            
            for item in section.get("rows", []):
                try:
                    ipo = self._parse_nasdaq_item(item, section_name)
                    if ipo:
                        ipos.append(ipo)
                except Exception:
                    continue
        
        return ipos

    def _parse_nasdaq_item(self, item: Dict[str, Any], section: str) -> Optional[IPODetails]:
        """Parse a single NASDAQ IPO calendar row."""
        symbol = (
            item.get("proposedTickerSymbol") 
            or item.get("symbol") 
            or item.get("proposedSymbol")
            or ""
        ).upper().strip()
        
        if not symbol:
            return None
        
        exchange_raw = (item.get("proposedExchange") or item.get("exchange") or "").upper()
        exchange = Exchange.NASDAQ
        if "NYSE" in exchange_raw:
            exchange = Exchange.NYSE
        
        # Determine status from section
        status_map = {
            "filed": IPOStatus.FILED,
            "upcoming": IPOStatus.NOT_ANNOUNCED,
            "priced": IPOStatus.PRICED,
            "withdrawn": IPOStatus.WITHDRAWN,
        }
        status = status_map.get(section, IPOStatus.NOT_ANNOUNCED)
        
        # Parse dates
        expected_date = self._parse_date(
            item.get("expectedDate") 
            or item.get("pricedDate") 
            or item.get("filedDate")
        )
        priced_date = self._parse_date(item.get("pricedDate"))
        listed_date = self._parse_date(item.get("listedDate") or item.get("expectedDate"))
        
        # Parse price range
        price_range = None
        offer_price = None
        price_raw = (item.get("proposedSharePrice") or "").replace(",", "").strip()
        if price_raw:
            try:
                amount = Decimal(price_raw)
                offer_price = Money(amount, "USD")
                price_range = PriceRange(low=offer_price, high=offer_price)
            except Exception:
                pass
        
        # Parse shares offered
        shares_offered = None
        shares_raw = (item.get("sharesOffered") or "").replace(",", "").strip()
        if shares_raw:
            try:
                shares_offered = int(Decimal(shares_raw))
            except Exception:
                pass
        
        # Parse company name
        company_name = item.get("companyName") or item.get("name") or ""
        
        return IPODetails(
            symbol=symbol,
            company_name=company_name,
            exchange=exchange,
            expected_date=expected_date,
            priced_date=priced_date,
            listed_date=listed_date,
            status=status.value,
            shares_offered=shares_offered,
            price_range=price_range,
            offer_price=offer_price,
            sector=self._map_sector(item.get("sector", "")),
            industry=self._map_industry(item.get("industry", "")),
        )

    def _map_sector(self, sector: str) -> Sector:
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

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        raw = str(value).strip()
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d-%b-%Y", "%d %b %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        """Fetch recently listed IPOs from NASDAQ."""
        result = await self.fetch_upcoming(lookahead_days=days)
        if result.success and result.data:
            cutoff = datetime.utcnow().date()
            recent = [
                ipo for ipo in result.data
                if ipo.listed_date and ipo.listed_date.date() >= cutoff
            ]
            result.data = recent
        return result

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")


class NYSEProvider(IPODataProvider):
    """Provider for NYSE IPO calendar data."""

    def __init__(self):
        config = ProviderConfig(
            name="nyse",
            base_url="https://www.nyse.com",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=60,
            headers={
                "User-Agent": "IPO Intelligence Agent/1.0",
                "Accept": "application/json",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/api/ipo/calendar", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"NYSE API returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/ipo/calendar",
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"NYSE API returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="nyse.com",
                )
            
            data = response.json()
            ipos = self._parse_nyse_data(data)
            
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="nyse.com",
                source_reference="https://www.nyse.com/api/ipo/calendar",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="nyse.com",
            )

    def _parse_nyse_data(self, data: Dict[str, Any]) -> List[IPODetails]:
        ipos = []
        for item in data.get("upcoming", []):
            try:
                ipo = self._parse_nyse_item(item)
                if ipo:
                    ipos.append(ipo)
            except Exception:
                continue
        return ipos

    def _parse_nyse_item(self, item: Dict[str, Any]) -> Optional[IPODetails]:
        symbol = item.get("symbol", "").upper()
        if not symbol:
            return None
        
        expected_date = None
        if item.get("expectedDate"):
            try:
                expected_date = datetime.fromisoformat(item["expectedDate"])
            except Exception:
                pass
        
        price_range = None
        if item.get("priceLow") and item.get("priceHigh"):
            try:
                low = Money(Decimal(str(item["priceLow"])), "USD")
                high = Money(Decimal(str(item["priceHigh"])), "USD")
                price_range = PriceRange(low=low, high=high)
            except Exception:
                pass
        
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

    def _map_sector(self, sector: str) -> Sector:
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

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=days)
        if result.success and result.data:
            cutoff = datetime.utcnow().date()
            recent = [
                ipo for ipo in result.data
                if ipo.listed_date and ipo.listed_date.date() >= cutoff
            ]
            result.data = recent
        return result

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")


class SECEdgarProvider(IPODataProvider):
    """Provider for SEC EDGAR S-1/F-1 filings."""

    def __init__(self):
        config = ProviderConfig(
            name="sec_edgar",
            base_url="https://efts.sec.gov",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=10,  # SEC has strict rate limits
            headers={
                "User-Agent": "IPO Intelligence Research dev@example.com",
                "Accept": "application/json",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/LATEST/search-index", params={"q": "S-1", "forms": "S-1"}, timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"SEC EDGAR returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        try:
            client = await self._get_client()
            cutoff = datetime.utcnow() - timedelta(days=lookahead_days)
            
            response = await client.get(
                "/LATEST/search-index",
                params={
                    "q": '"S-1" OR "F-1"',
                    "forms": "S-1,F-1",
                    "dateRange": "m",  # Last month
                },
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"SEC EDGAR returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="sec.gov",
                )
            
            data = response.json()
            ipos = self._parse_sec_data(data, cutoff)
            
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="sec.gov",
                source_reference="https://efts.sec.gov/LATEST/search-index",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="sec.gov",
            )

    def _parse_sec_data(self, data: Dict[str, Any], cutoff: datetime) -> List[IPODetails]:
        ipos = []
        hits = data.get("hits", {}).get("hits", []) or []
        
        for hit in hits:
            src = hit.get("_source", {})
            if not isinstance(src, dict):
                continue
            
            form = str(src.get("form", ""))
            root_form = form.split("/")[0]
            if root_form not in ("S-1", "F-1"):
                continue
            
            file_date = self._parse_date(src.get("file_date"))
            if not file_date or file_date < cutoff:
                continue
            
            display_names = src.get("display_names") or []
            if not display_names:
                continue
            
            name = str(display_names[0]).split(" (CIK")[0].strip()
            
            # Extract ticker from name
            ticker_match = re.search(r"\(\s*([A-Z0-9]{1,12})(?:[,\s/]|\))", name)
            symbol = (ticker_match.group(1) if ticker_match else self._to_symbol(name)).upper()
            
            # Clean name
            name = re.sub(r"\s*\([^)]*[A-Z0-9][^)]*\)\s*$", "", name).strip()
            
            if not symbol:
                continue
            
            ipos.append(IPODetails(
                symbol=symbol,
                company_name=name,
                exchange=Exchange.OTHER,  # Will be determined from filing
                expected_date=file_date,
                status=IPOStatus.FILED.value,
                sector=Sector.UNCLASSIFIED,
                industry=Industry.OTHER,
            ))
        
        return ipos

    def _to_symbol(self, name: str) -> str:
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        if len(cleaned) > 20:
            cleaned = cleaned[:20]
        return cleaned

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        raw = str(value).strip()
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d-%b-%Y", "%d %b %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=days)
        if result.success and result.data:
            cutoff = datetime.utcnow().date()
            recent = [
                ipo for ipo in result.data
                if ipo.listed_date and ipo.listed_date.date() >= cutoff
            ]
            result.data = recent
        return result

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")


class RenaissanceCapitalProvider(IPODataProvider):
    """Provider for Renaissance Capital IPO calendar."""

    def __init__(self):
        config = ProviderConfig(
            name="renaissance",
            base_url="https://www.renaissancecapital.com",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=20,
            headers={
                "User-Agent": "IPO Intelligence Agent/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/ipo-calendar", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"Renaissance Capital returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        try:
            client = await self._get_client()
            response = await client.get("/ipo-calendar", timeout=30.0)
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"Renaissance Capital returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="renaissancecapital.com",
                )
            
            soup = BeautifulSoup(response.text, "html.parser")
            ipos = self._parse_calendar(soup)
            
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="renaissancecapital.com",
                source_reference="https://www.renaissancecapital.com/ipo-calendar",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="SCRAPE_ERROR",
                source="renaissancecapital.com",
            )

    def _parse_calendar(self, soup: BeautifulSoup) -> List[IPODetails]:
        """Parse Renaissance Capital IPO calendar HTML."""
        ipos = []
        # Find the calendar table
        table = soup.find("table", {"id": "ipo-calendar"}) or soup.find("table", class_=re.compile(r"calendar|ipo"))
        if not table:
            # Try finding by content
            tables = soup.find_all("table")
            for t in tables:
                if t.find("th", string=re.compile(r"company|symbol|date|price", re.I)):
                    table = t
                    break
        
        if not table:
            return ipos
        
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            
            try:
                company_name = cols[0].get_text(strip=True)
                symbol_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                symbol = self._extract_symbol(company_name, symbol_text)
                
                # Determine exchange
                exchange = Exchange.NASDAQ  # Default
                if len(cols) > 2:
                    exchange_text = cols[2].get_text(strip=True).upper()
                    if "NYSE" in exchange_text:
                        exchange = Exchange.NYSE
                
                expected_date = self._parse_date(cols[3].get_text(strip=True)) if len(cols) > 3 else None
                
                ipo = IPODetails(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=exchange,
                    expected_date=expected_date,
                    status=IPOStatus.NOT_ANNOUNCED.value,
                    sector=Sector.UNCLASSIFIED,
                    industry=Industry.OTHER,
                )
                ipos.append(ipo)
            except Exception:
                continue
        return ipos

    def _extract_symbol(self, name: str, symbol_col: str) -> str:
        if symbol_col and re.match(r"^[A-Z]{1,5}$", symbol_col.upper()):
            return symbol_col.upper()
        match = re.search(r"\(([A-Z]{1,5})\)", name)
        if match:
            return match.group(1)
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        return cleaned[:20] if cleaned else "UNKNOWN"

    def _parse_date(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%m/%d/%Y", "%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=days)
        if result.success and result.data:
            cutoff = datetime.utcnow().date()
            recent = [
                ipo for ipo in result.data
                if ipo.listed_date and ipo.listed_date.date() >= cutoff
            ]
            result.data = recent
        return result

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")