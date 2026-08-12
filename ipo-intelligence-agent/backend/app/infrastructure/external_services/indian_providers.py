"""Indian IPO data providers."""

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


class InvestorGainProvider(IPODataProvider):
    """Provider for Indian IPO data from InvestorGain.com (GMP data)."""

    def __init__(self):
        config = ProviderConfig(
            name="investorgain",
            base_url="https://webnodejs.investorgain.com",
            timeout_seconds=60,
            max_retries=3,
            rate_limit_per_minute=30,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)
        self._hosts = [
            "webnodejs.investorgain.com",
            "alphanodejs.investorgain.com",
        ]

    async def _check_health(self) -> None:
        """Check if InvestorGain API is accessible."""
        for host in self._hosts:
            try:
                client = await self._get_client()
                # Just check if we can reach the host
                response = await client.get(
                    f"https://{host}/cloud/v2/report/data-read/331/1/1/2024/24-25/0/all?search=",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("msg") == 1:
                        return
            except Exception:
                continue
        raise Exception("All InvestorGain hosts unavailable")

    def _get_financial_year(self) -> str:
        """Calculate current Indian financial year (Apr-Mar)."""
        now = datetime.utcnow()
        if now.month >= 4:
            return f"{now.year}-{str(now.year + 1)[-2:]}"
        return f"{now.year - 1}-{str(now.year)[-2:]}"

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        """Fetch upcoming Indian IPOs with GMP data."""
        fy = self._get_financial_year()
        now = datetime.utcnow()
        errors = []

        for host in self._hosts:
            url = (
                f"https://{host}/cloud/v2/report/data-read/331/1/"
                f"{now.month}/{now.year}/{fy}/0/all?search="
            )
            try:
                client = await self._get_client()
                response = await client.get(url, timeout=60.0)
                
                if response.status_code != 200:
                    errors.append(f"{host}: HTTP {response.status_code}")
                    continue
                
                data = response.json()
                if data.get("msg") != 1:
                    errors.append(f"{host}: Unexpected response format")
                    continue
                
                ipos = []
                for item in data.get("reportTableData", []):
                    ipo = self._parse_item(item, url)
                    if ipo:
                        # Filter by exchange if specified
                        if exchange and ipo.exchange.value != exchange:
                            continue
                        ipos.append(ipo)
                
                return ProviderResult(
                    success=True,
                    data=ipos,
                    source="investorgain.com",
                    source_reference=url,
                )
                
            except Exception as e:
                errors.append(f"{host}: {str(e)}")
                continue
        
        return ProviderResult(
            success=False,
            error="; ".join(errors),
            error_type="ALL_HOSTS_FAILED",
            source="investorgain.com",
        )

    def _parse_item(self, item: Dict[str, Any], source_url: str) -> Optional[IPODetails]:
        """Parse a single InvestorGain IPO item."""
        try:
            name = (item.get("~ipo_name") or "").strip()
            if not name:
                return None
            
            symbol = self._to_symbol(name)
            if not symbol:
                return None
            
            name_html = item.get("Name", "")
            category = (item.get("~IPO_Category") or "").upper()
            
            exchange = Exchange.NSE
            if "BSE" in name_html.upper():
                exchange = Exchange.BSE
            
            today = datetime.utcnow().date()
            expected_date = self._parse_date(item.get("~Srt_Open"))
            close_date = self._parse_date(item.get("~Srt_Close"))
            listing_date = self._parse_date(item.get("~Str_Listing"))
            
            # Determine status
            status = IPOStatus.NOT_ANNOUNCED
            if listing_date and listing_date.date() < today:
                status = IPOStatus.LISTED
            elif expected_date:
                status = IPOStatus.FILED
            elif close_date and close_date.date() < today:
                status = IPOStatus.PRICED
            
            # Parse price range
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
                    pass
            
            expected_raise = self._parse_size(item.get("IPO Size"))
            
            # Parse lot size
            lot_size = None
            lot_raw = (item.get("Lot Size") or "").strip()
            if lot_raw:
                try:
                    lot_size = int(lot_raw.replace(",", ""))
                except Exception:
                    pass
            
            try:
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
                    sector=self._classify_sector(name),
                    industry=self._classify_industry(name),
                    lot_size=lot_size,
                    # Source attribution
                    source="investorgain.com",
                    source_reference=url,
                    source_updated_at=datetime.utcnow(),
                    collector_version="1.0.0",
                    data_quality_score=0.7,  # Moderate - InvestorGain provides basic IPO data but no financials
                )
            except Exception:
                return None
        except Exception:
            return None

    @staticmethod
    def _classify_sector(name: str) -> Sector:
        """Classify sector based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['tech', 'software', 'system', 'digital', 'data', 'cloud', 'cyber', 'ai', 'it ', 'information']):
            return Sector.INFORMATION_TECHNOLOGY
        
        # Healthcare
        if any(kw in name_lower for kw in ['pharma', 'biotech', 'health', 'medical', 'hospital', 'diagnostic', 'drug', 'medicine', 'life science']):
            return Sector.HEALTH_CARE
        
        # Financial
        if any(kw in name_lower for kw in ['bank', 'finance', 'capital', 'investment', 'insurance', 'credit', 'loan', 'fintech', 'payment', 'wealth']):
            return Sector.FINANCIALS
        
        # Consumer Discretionary
        if any(kw in name_lower for kw in ['retail', 'consumer', 'fashion', 'apparel', 'footwear', 'jewel', 'auto', 'vehicle', 'travel', 'hotel', 'restaurant', 'food service']):
            return Sector.CONSUMER_DISCRETIONARY
        
        # Consumer Staples
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'grocery', 'fmcg', 'personal care', 'household']):
            return Sector.CONSUMER_STAPLES
        
        # Industrials
        if any(kw in name_lower for kw in ['engineering', 'manufacturing', 'industrial', 'construction', 'infrastructure', 'logistics', 'transport', 'cargo', 'shipping', 'transmission', 'power', 'energy', 'electrical', 'mechanical', 'machinery']):
            return Sector.INDUSTRIALS
        
        # Materials
        if any(kw in name_lower for kw in ['chemical', 'cement', 'steel', 'metal', 'mining', 'mineral', 'aluminium', 'copper', 'zinc', 'paper', 'packaging']):
            return Sector.MATERIALS
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum', 'refinery', 'solar', 'renewable', 'wind', 'hydro']):
            return Sector.ENERGY
        
        # Real Estate
        if any(kw in name_lower for kw in ['realty', 'real estate', 'property', 'developer', 'construction', 'housing', 'infra']):
            return Sector.REAL_ESTATE
        
        # Utilities
        if any(kw in name_lower for kw in ['utility', 'electric', 'power', 'water', 'gas distribution']):
            return Sector.UTILITIES
        
        # Communication Services
        if any(kw in name_lower for kw in ['telecom', 'communication', 'media', 'broadcast', 'entertainment', 'gaming']):
            return Sector.COMMUNICATION_SERVICES
        
        return Sector.UNCLASSIFIED

    @staticmethod
    def _classify_industry(name: str) -> Industry:
        """Classify industry based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['software', 'saas', 'platform', 'app', 'digital', 'analytics', 'cloud', 'cyber']):
            return Industry.SOFTWARE
        if any(kw in name_lower for kw in ['semi', 'chip', 'electronics', 'hardware']):
            return Industry.SEMICONDUCTORS
        if any(kw in name_lower for kw in ['it service', 'consulting', 'outsourcing']):
            return Industry.IT_SERVICES
        if any(kw in name_lower for kw in ['ai', 'machine learning', 'ml ', 'artificial intelligence']):
            return Industry.AI_ML
        if any(kw in name_lower for kw in ['cyber', 'security']):
            return Industry.CYBERSECURITY
        if any(kw in name_lower for kw in ['fintech', 'payment', 'wallet']):
            return Industry.FINTECH
        if any(kw in name_lower for kw in ['ecommerce', 'e-commerce', 'marketplace', 'online']):
            return Industry.ECOMMERCE
        
        # Healthcare
        if any(kw in name_lower for kw in ['biotech', 'biotechnology']):
            return Industry.BIOTECH
        if any(kw in name_lower for kw in ['pharma', 'pharmaceutical']):
            return Industry.PHARMACEUTICALS
        if any(kw in name_lower for kw in ['medical device', 'diagnostic']):
            return Industry.MEDICAL_DEVICES
        if any(kw in name_lower for kw in ['hospital', 'healthcare service']):
            return Industry.HEALTHCARE_SERVICES
        if any(kw in name_lower for kw in ['diagnostic']):
            return Industry.DIAGNOSTICS
        
        # Financial
        if any(kw in name_lower for kw in ['bank']):
            return Industry.BANKING
        if any(kw in name_lower for kw in ['insurance']):
            return Industry.INSURANCE
        if any(kw in name_lower for kw in ['asset management', 'mutual fund', 'wealth']):
            return Industry.ASSET_MANAGEMENT
        if any(kw in name_lower for kw in ['payment', 'gateway']):
            return Industry.PAYMENTS
        
        # Consumer
        if any(kw in name_lower for kw in ['retail', 'store', 'shop']):
            return Industry.RETAIL
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'restaurant']):
            return Industry.FOOD_BEVERAGE
        if any(kw in name_lower for kw in ['apparel', 'garment', 'textile', 'fashion']):
            return Industry.APPAREL
        if any(kw in name_lower for kw in ['auto', 'vehicle', 'car', 'ev ', 'electric vehicle']):
            return Industry.AUTOMOTIVE
        
        # Industrial
        if any(kw in name_lower for kw in ['aerospace', 'aviation', 'defense']):
            return Industry.AEROSPACE
        if any(kw in name_lower for kw in ['manufacturing', 'factory', 'production']):
            return Industry.MANUFACTURING
        if any(kw in name_lower for kw in ['logistics', 'supply chain', 'transport', 'cargo', 'shipping']):
            return Industry.LOGISTICS
        if any(kw in name_lower for kw in ['construction', 'infra', 'infrastructure']):
            return Industry.CONSTRUCTION
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum']):
            return Industry.OIL_GAS
        if any(kw in name_lower for kw in ['solar', 'wind', 'renewable', 'green energy']):
            return Industry.RENEWABLE_ENERGY
        
        # Materials
        if any(kw in name_lower for kw in ['chemical']):
            return Industry.CHEMICALS
        if any(kw in name_lower for kw in ['metal', 'mining', 'steel', 'aluminium', 'copper']):
            return Industry.METALS_MINING
        
        return Industry.OTHER

    @staticmethod
    def _to_symbol(name: str) -> str:
        """Convert IPO name to uppercase alphanumeric symbol."""
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        if len(cleaned) > 20:
            cleaned = cleaned[:20]
        return cleaned

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if not value:
            return None
        raw = str(value).strip()
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d-%b-%Y", "%d %b %Y"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
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
            multiplier = {
                "CR": Decimal("10000000"),
                "CRORE": Decimal("10000000"),
                "L": Decimal("100000"),
                "LAKH": Decimal("100000"),
                "K": Decimal("1000"),
            }.get(unit, Decimal("1"))
            return Money(number * multiplier, "INR")
        except Exception:
            return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        """Fetch recently listed IPOs."""
        result = await self.fetch_upcoming(lookahead_days=days)
        if result.success and result.data:
            cutoff = datetime.utcnow().date()
            # Filter to only listed IPOs within the timeframe
            recent = [
                ipo for ipo in result.data
                if ipo.listed_date and ipo.listed_date.date() >= cutoff
            ]
            result.data = recent
        return result

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        """Fetch specific IPO by symbol."""
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(
                        success=True,
                        data=ipo,
                        source=result.source,
                        source_reference=result.source_reference,
                    )
        return ProviderResult(
            success=False,
            error=f"IPO not found: {symbol}",
            error_type="NOT_FOUND",
        )


class NSEIndiaProvider(IPODataProvider):
    """Provider for NSE India IPO data."""

    def __init__(self):
        config = ProviderConfig(
            name="nse_india",
            base_url="https://www.nseindia.com",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=30,
            headers={
                "User-Agent": "IPO Intelligence Agent/1.0",
                "Accept": "application/json, text/plain, */*",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        """Check NSE India API accessibility."""
        client = await self._get_client()
        # Try to access the NSE IPO page
        response = await client.get("/api/ipo/upcoming", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"NSE API returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        """Fetch upcoming IPOs from NSE India."""
        try:
            client = await self._get_client()
            response = await client.get("/api/ipo/upcoming", timeout=30.0)
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"NSE API returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="nseindia.com",
                )
            
            data = response.json()
            ipos = self._parse_nse_data(data)
            
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="nseindia.com",
                source_reference="https://www.nseindia.com/api/ipo/upcoming",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="nseindia.com",
            )

    def _parse_nse_data(self, data: Dict[str, Any]) -> List[IPODetails]:
        """Parse NSE IPO API response."""
        ipos = []
        # NSE API structure may vary - this is a template
        for item in data.get("data", []):
            try:
                symbol = (item.get("symbol") or item.get("SYMBOL") or "").upper().strip()
                if not symbol:
                    continue
                
                company_name = item.get("companyName") or item.get("COMPANY_NAME") or ""
                
                ipo = IPODetails(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=Exchange.NSE,
                    expected_date=self._parse_date(item.get("openDate") or item.get("OPEN_DATE")),
                    listed_date=self._parse_date(item.get("listingDate") or item.get("LISTING_DATE")),
                    status=self._map_status(item.get("status") or item.get("STATUS")),
                    price_range=self._parse_price_range(item),
                    shares_offered=self._parse_int(item.get("issueSize") or item.get("ISSUE_SIZE")),
                    sector=self._classify_sector(company_name),
                    industry=self._classify_industry(company_name),
                    # Source attribution
                    source="nseindia.com",
                    source_reference="https://www.nseindia.com/api/ipo/upcoming",
                    source_updated_at=datetime.utcnow(),
                    collector_version="1.0.0",
                    data_quality_score=0.8,  # High - official exchange data
                )
                ipos.append(ipo)
            except Exception:
                continue
        return ipos

    @staticmethod
    def _classify_sector(name: str) -> Sector:
        """Classify sector based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['tech', 'software', 'system', 'digital', 'data', 'cloud', 'cyber', 'ai', 'it ', 'information']):
            return Sector.INFORMATION_TECHNOLOGY
        
        # Healthcare
        if any(kw in name_lower for kw in ['pharma', 'biotech', 'health', 'medical', 'hospital', 'diagnostic', 'drug', 'medicine', 'life science']):
            return Sector.HEALTH_CARE
        
        # Financial
        if any(kw in name_lower for kw in ['bank', 'finance', 'capital', 'investment', 'insurance', 'credit', 'loan', 'fintech', 'payment', 'wealth']):
            return Sector.FINANCIALS
        
        # Consumer Discretionary
        if any(kw in name_lower for kw in ['retail', 'consumer', 'fashion', 'apparel', 'footwear', 'jewel', 'auto', 'vehicle', 'travel', 'hotel', 'restaurant', 'food service']):
            return Sector.CONSUMER_DISCRETIONARY
        
        # Consumer Staples
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'grocery', 'fmcg', 'personal care', 'household']):
            return Sector.CONSUMER_STAPLES
        
        # Industrials
        if any(kw in name_lower for kw in ['engineering', 'manufacturing', 'industrial', 'construction', 'infrastructure', 'logistics', 'transport', 'cargo', 'shipping', 'transmission', 'power', 'energy', 'electrical', 'mechanical', 'machinery']):
            return Sector.INDUSTRIALS
        
        # Materials
        if any(kw in name_lower for kw in ['chemical', 'cement', 'steel', 'metal', 'mining', 'mineral', 'aluminium', 'copper', 'zinc', 'paper', 'packaging']):
            return Sector.MATERIALS
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum', 'refinery', 'solar', 'renewable', 'wind', 'hydro']):
            return Sector.ENERGY
        
        # Real Estate
        if any(kw in name_lower for kw in ['realty', 'real estate', 'property', 'developer', 'construction', 'housing', 'infra']):
            return Sector.REAL_ESTATE
        
        # Utilities
        if any(kw in name_lower for kw in ['utility', 'electric', 'power', 'water', 'gas distribution']):
            return Sector.UTILITIES
        
        # Communication Services
        if any(kw in name_lower for kw in ['telecom', 'communication', 'media', 'broadcast', 'entertainment', 'gaming']):
            return Sector.COMMUNICATION_SERVICES
        
        return Sector.UNCLASSIFIED

    @staticmethod
    def _classify_industry(name: str) -> Industry:
        """Classify industry based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['software', 'saas', 'platform', 'app', 'digital', 'analytics', 'cloud', 'cyber']):
            return Industry.SOFTWARE
        if any(kw in name_lower for kw in ['semi', 'chip', 'electronics', 'hardware']):
            return Industry.SEMICONDUCTORS
        if any(kw in name_lower for kw in ['it service', 'consulting', 'outsourcing']):
            return Industry.IT_SERVICES
        if any(kw in name_lower for kw in ['ai', 'machine learning', 'ml ', 'artificial intelligence']):
            return Industry.AI_ML
        if any(kw in name_lower for kw in ['cyber', 'security']):
            return Industry.CYBERSECURITY
        if any(kw in name_lower for kw in ['fintech', 'payment', 'wallet']):
            return Industry.FINTECH
        if any(kw in name_lower for kw in ['ecommerce', 'e-commerce', 'marketplace', 'online']):
            return Industry.ECOMMERCE
        
        # Healthcare
        if any(kw in name_lower for kw in ['biotech', 'biotechnology']):
            return Industry.BIOTECH
        if any(kw in name_lower for kw in ['pharma', 'pharmaceutical']):
            return Industry.PHARMACEUTICALS
        if any(kw in name_lower for kw in ['medical device', 'diagnostic']):
            return Industry.MEDICAL_DEVICES
        if any(kw in name_lower for kw in ['hospital', 'healthcare service']):
            return Industry.HEALTHCARE_SERVICES
        if any(kw in name_lower for kw in ['diagnostic']):
            return Industry.DIAGNOSTICS
        
        # Financial
        if any(kw in name_lower for kw in ['bank']):
            return Industry.BANKING
        if any(kw in name_lower for kw in ['insurance']):
            return Industry.INSURANCE
        if any(kw in name_lower for kw in ['asset management', 'mutual fund', 'wealth']):
            return Industry.ASSET_MANAGEMENT
        if any(kw in name_lower for kw in ['payment', 'gateway']):
            return Industry.PAYMENTS
        
        # Consumer
        if any(kw in name_lower for kw in ['retail', 'store', 'shop']):
            return Industry.RETAIL
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'restaurant']):
            return Industry.FOOD_BEVERAGE
        if any(kw in name_lower for kw in ['apparel', 'garment', 'textile', 'fashion']):
            return Industry.APPAREL
        if any(kw in name_lower for kw in ['auto', 'vehicle', 'car', 'ev ', 'electric vehicle']):
            return Industry.AUTOMOTIVE
        
        # Industrial
        if any(kw in name_lower for kw in ['aerospace', 'aviation', 'defense']):
            return Industry.AEROSPACE
        if any(kw in name_lower for kw in ['manufacturing', 'factory', 'production']):
            return Industry.MANUFACTURING
        if any(kw in name_lower for kw in ['logistics', 'supply chain', 'transport', 'cargo', 'shipping']):
            return Industry.LOGISTICS
        if any(kw in name_lower for kw in ['construction', 'infra', 'infrastructure']):
            return Industry.CONSTRUCTION
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum']):
            return Industry.OIL_GAS
        if any(kw in name_lower for kw in ['solar', 'wind', 'renewable', 'green energy']):
            return Industry.RENEWABLE_ENERGY
        
        # Materials
        if any(kw in name_lower for kw in ['chemical']):
            return Industry.CHEMICALS
        if any(kw in name_lower for kw in ['metal', 'mining', 'steel', 'aluminium', 'copper']):
            return Industry.METALS_MINING
        
        return Industry.OTHER

    def _map_status(self, status: Optional[str]) -> str:
        """Map NSE status to IPOStatus."""
        if not status:
            return IPOStatus.NOT_ANNOUNCED.value
        status_upper = status.upper()
        if "LISTED" in status_upper:
            return IPOStatus.LISTED.value
        if "OPEN" in status_upper or "SUBSCRIPTION" in status_upper:
            return IPOStatus.PRICED.value
        if "CLOSED" in status_upper:
            return IPOStatus.FILED.value
        return IPOStatus.NOT_ANNOUNCED.value

    def _parse_price_range(self, item: Dict[str, Any]) -> Optional[PriceRange]:
        """Parse price range from NSE item."""
        low = item.get("priceLow") or item.get("PRICE_LOW")
        high = item.get("priceHigh") or item.get("PRICE_HIGH")
        if low is not None and high is not None:
            try:
                return PriceRange(
                    low=Money(Decimal(str(low)), "INR"),
                    high=Money(Decimal(str(high)), "INR"),
                )
            except Exception:
                pass
        return None

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        raw = str(value).strip()
        for fmt in ("%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d", "%b %d, %Y"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    def _parse_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value).replace(",", "").strip())
        except Exception:
            return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        """Fetch recent NSE IPOs."""
        # NSE may have a separate endpoint for listed IPOs
        return await self.fetch_upcoming(lookahead_days=days)

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")


class BSEIndiaProvider(IPODataProvider):
    """Provider for BSE India IPO data."""

    def __init__(self):
        config = ProviderConfig(
            name="bse_india",
            base_url="https://api.bseindia.com",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=30,
            headers={
                "User-Agent": "IPO Intelligence Agent/1.0",
                "Accept": "application/json",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/BseIndiaAPI/api/IPO/GetIPOList", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"BSE API returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        try:
            client = await self._get_client()
            response = await client.get(
                "/BseIndiaAPI/api/IPO/GetIPOList",
                params={"Type": "U"},  # U = Upcoming
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"BSE API returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="bseindia.com",
                )
            
            data = response.json()
            ipos = self._parse_bse_data(data)
            
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="bseindia.com",
                source_reference="https://api.bseindia.com/BseIndiaAPI/api/IPO/GetIPOList",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="bseindia.com",
            )

    def _parse_bse_data(self, data: Any) -> List[IPODetails]:
        ipos = []
        if isinstance(data, dict):
            data = data.get("Table", [])
        elif not isinstance(data, list):
            return ipos
        
        for item in data:
            try:
                symbol = (item.get("SCRIP_CD") or "").strip()
                if not symbol:
                    continue
                
                company_name = item.get("COMPANY_NAME") or ""
                
                ipo = IPODetails(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=Exchange.BSE,
                    expected_date=self._parse_date(item.get("OPEN_DATE")),
                    listed_date=self._parse_date(item.get("LISTING_DATE")),
                    status=self._map_status(item.get("STATUS")),
                    price_range=self._parse_price_range(item),
                    shares_offered=self._parse_int(item.get("ISSUE_SIZE")),
                    sector=self._classify_sector(company_name),
                    industry=self._classify_industry(company_name),
                    # Source attribution
                    source="bseindia.com",
                    source_reference="https://api.bseindia.com/BseIndiaAPI/api/IPO/GetIPOList",
                    source_updated_at=datetime.utcnow(),
                    collector_version="1.0.0",
                    data_quality_score=0.8,  # High - official exchange data
                )
                ipos.append(ipo)
            except Exception:
                continue
        return ipos

    @staticmethod
    def _classify_sector(name: str) -> Sector:
        """Classify sector based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['tech', 'software', 'system', 'digital', 'data', 'cloud', 'cyber', 'ai', 'it ', 'information']):
            return Sector.INFORMATION_TECHNOLOGY
        
        # Healthcare
        if any(kw in name_lower for kw in ['pharma', 'biotech', 'health', 'medical', 'hospital', 'diagnostic', 'drug', 'medicine', 'life science']):
            return Sector.HEALTH_CARE
        
        # Financial
        if any(kw in name_lower for kw in ['bank', 'finance', 'capital', 'investment', 'insurance', 'credit', 'loan', 'fintech', 'payment', 'wealth']):
            return Sector.FINANCIALS
        
        # Consumer Discretionary
        if any(kw in name_lower for kw in ['retail', 'consumer', 'fashion', 'apparel', 'footwear', 'jewel', 'auto', 'vehicle', 'travel', 'hotel', 'restaurant', 'food service']):
            return Sector.CONSUMER_DISCRETIONARY
        
        # Consumer Staples
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'grocery', 'fmcg', 'personal care', 'household']):
            return Sector.CONSUMER_STAPLES
        
        # Industrials
        if any(kw in name_lower for kw in ['engineering', 'manufacturing', 'industrial', 'construction', 'infrastructure', 'logistics', 'transport', 'cargo', 'shipping', 'transmission', 'power', 'energy', 'electrical', 'mechanical', 'machinery']):
            return Sector.INDUSTRIALS
        
        # Materials
        if any(kw in name_lower for kw in ['chemical', 'cement', 'steel', 'metal', 'mining', 'mineral', 'aluminium', 'copper', 'zinc', 'paper', 'packaging']):
            return Sector.MATERIALS
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum', 'refinery', 'solar', 'renewable', 'wind', 'hydro']):
            return Sector.ENERGY
        
        # Real Estate
        if any(kw in name_lower for kw in ['realty', 'real estate', 'property', 'developer', 'construction', 'housing', 'infra']):
            return Sector.REAL_ESTATE
        
        # Utilities
        if any(kw in name_lower for kw in ['utility', 'electric', 'power', 'water', 'gas distribution']):
            return Sector.UTILITIES
        
        # Communication Services
        if any(kw in name_lower for kw in ['telecom', 'communication', 'media', 'broadcast', 'entertainment', 'gaming']):
            return Sector.COMMUNICATION_SERVICES
        
        return Sector.UNCLASSIFIED

    @staticmethod
    def _classify_industry(name: str) -> Industry:
        """Classify industry based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['software', 'saas', 'platform', 'app', 'digital', 'analytics', 'cloud', 'cyber']):
            return Industry.SOFTWARE
        if any(kw in name_lower for kw in ['semi', 'chip', 'electronics', 'hardware']):
            return Industry.SEMICONDUCTORS
        if any(kw in name_lower for kw in ['it service', 'consulting', 'outsourcing']):
            return Industry.IT_SERVICES
        if any(kw in name_lower for kw in ['ai', 'machine learning', 'ml ', 'artificial intelligence']):
            return Industry.AI_ML
        if any(kw in name_lower for kw in ['cyber', 'security']):
            return Industry.CYBERSECURITY
        if any(kw in name_lower for kw in ['fintech', 'payment', 'wallet']):
            return Industry.FINTECH
        if any(kw in name_lower for kw in ['ecommerce', 'e-commerce', 'marketplace', 'online']):
            return Industry.ECOMMERCE
        
        # Healthcare
        if any(kw in name_lower for kw in ['biotech', 'biotechnology']):
            return Industry.BIOTECH
        if any(kw in name_lower for kw in ['pharma', 'pharmaceutical']):
            return Industry.PHARMACEUTICALS
        if any(kw in name_lower for kw in ['medical device', 'diagnostic']):
            return Industry.MEDICAL_DEVICES
        if any(kw in name_lower for kw in ['hospital', 'healthcare service']):
            return Industry.HEALTHCARE_SERVICES
        if any(kw in name_lower for kw in ['diagnostic']):
            return Industry.DIAGNOSTICS
        
        # Financial
        if any(kw in name_lower for kw in ['bank']):
            return Industry.BANKING
        if any(kw in name_lower for kw in ['insurance']):
            return Industry.INSURANCE
        if any(kw in name_lower for kw in ['asset management', 'mutual fund', 'wealth']):
            return Industry.ASSET_MANAGEMENT
        if any(kw in name_lower for kw in ['payment', 'gateway']):
            return Industry.PAYMENTS
        
        # Consumer
        if any(kw in name_lower for kw in ['retail', 'store', 'shop']):
            return Industry.RETAIL
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'restaurant']):
            return Industry.FOOD_BEVERAGE
        if any(kw in name_lower for kw in ['apparel', 'garment', 'textile', 'fashion']):
            return Industry.APPAREL
        if any(kw in name_lower for kw in ['auto', 'vehicle', 'car', 'ev ', 'electric vehicle']):
            return Industry.AUTOMOTIVE
        
        # Industrial
        if any(kw in name_lower for kw in ['aerospace', 'aviation', 'defense']):
            return Industry.AEROSPACE
        if any(kw in name_lower for kw in ['manufacturing', 'factory', 'production']):
            return Industry.MANUFACTURING
        if any(kw in name_lower for kw in ['logistics', 'supply chain', 'transport', 'cargo', 'shipping']):
            return Industry.LOGISTICS
        if any(kw in name_lower for kw in ['construction', 'infra', 'infrastructure']):
            return Industry.CONSTRUCTION
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum']):
            return Industry.OIL_GAS
        if any(kw in name_lower for kw in ['solar', 'wind', 'renewable', 'green energy']):
            return Industry.RENEWABLE_ENERGY
        
        # Materials
        if any(kw in name_lower for kw in ['chemical']):
            return Industry.CHEMICALS
        if any(kw in name_lower for kw in ['metal', 'mining', 'steel', 'aluminium', 'copper']):
            return Industry.METALS_MINING
        
        return Industry.OTHER

    def _map_status(self, status: Optional[str]) -> str:
        if not status:
            return IPOStatus.NOT_ANNOUNCED.value
        status_upper = status.upper()
        if "LISTED" in status_upper:
            return IPOStatus.LISTED.value
        if "OPEN" in status_upper:
            return IPOStatus.PRICED.value
        return IPOStatus.NOT_ANNOUNCED.value

    def _parse_price_range(self, item: Dict[str, Any]) -> Optional[PriceRange]:
        low = item.get("PRICE_LOW") or item.get("FLOOR_PRICE")
        high = item.get("PRICE_HIGH") or item.get("CAP_PRICE")
        if low is not None and high is not None:
            try:
                return PriceRange(
                    low=Money(Decimal(str(low)), "INR"),
                    high=Money(Decimal(str(high)), "INR"),
                )
            except Exception:
                pass
        return None

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        raw = str(value).strip()
        for fmt in ("%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    def _parse_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value).replace(",", "").strip())
        except Exception:
            return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        try:
            client = await self._get_client()
            response = await client.get(
                "/BseIndiaAPI/api/IPO/GetIPOList",
                params={"Type": "L"},  # L = Listed
                timeout=30.0,
            )
            if response.status_code != 200:
                return ProviderResult(success=False, error=f"HTTP {response.status_code}")
            
            data = response.json()
            ipos = self._parse_bse_data(data)
            cutoff = datetime.utcnow().date()
            recent = [ipo for ipo in ipos if ipo.listed_date and ipo.listed_date.date() >= cutoff]
            
            return ProviderResult(success=True, data=recent, source="bseindia.com")
        except Exception as e:
            return ProviderResult(success=False, error=str(e))

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")


class SEBIProvider(IPODataProvider):
    """Provider for SEBI DRHP/RHP filings."""

    def __init__(self):
        config = ProviderConfig(
            name="sebi",
            base_url="https://www.sebi.gov.in",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=20,
            headers={
                "User-Agent": "IPO Intelligence Research dev@example.com",
                "Accept": "application/json, text/html",
            },
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/sebiweb/home/list/3/4/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/P/0?type=3&category=4", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"SEBI returned {response.status_code}")

    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        """Fetch IPOs from SEBI filings (DRHP/RHP)."""
        try:
            client = await self._get_client()
            # SEBI public API for IPO filings
            response = await client.get(
                "/sebiweb/home/HomeController/getAllIPODetails",
                timeout=30.0,
            )
            
            if response.status_code != 200:
                # Try alternative approach - scrape the IPO page
                return await self._scrape_sebi_ipos()
            
            data = response.json()
            ipos = self._parse_sebi_data(data)
            
            if exchange:
                ipos = [ipo for ipo in ipos if ipo.exchange.value == exchange]
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="sebi.gov.in",
                source_reference="https://www.sebi.gov.in/sebiweb/home/HomeController/getAllIPODetails",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="SEBI_FETCH_ERROR",
                source="sebi.gov.in",
            )

    async def _scrape_sebi_ipos(self) -> ProviderResult[List[IPODetails]]:
        """Scrape SEBI IPO page for DRHP/RHP filings."""
        try:
            client = await self._get_client()
            response = await client.get(
                "/sebiweb/home/list/3/4/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/P/0?type=3&category=4",
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"SEBI page returned {response.status_code}",
                    error_type="HTTP_ERROR",
                )
            
            soup = BeautifulSoup(response.text, "html.parser")
            ipos = self._parse_sebi_html(soup)
            
            return ProviderResult(
                success=True,
                data=ipos,
                source="sebi.gov.in",
                source_reference="https://www.sebi.gov.in/sebiweb/home/list/3/4/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/P/0?type=3&category=4",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="SCRAPE_ERROR",
            )

    def _parse_sebi_html(self, soup: BeautifulSoup) -> List[IPODetails]:
        """Parse SEBI IPO listing HTML."""
        ipos = []
        # Find the IPO table
        table = soup.find("table", {"id": "ipoTable"}) or soup.find("table", class_="table")
        if not table:
            return ipos
        
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue
            
            try:
                company_name = cols[0].get_text(strip=True)
                symbol = self._extract_symbol(company_name)
                
                # Determine exchange from issuer details
                exchange = Exchange.NSE  # Default
                
                ipo = IPODetails(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=exchange,
                    expected_date=self._parse_date(cols[2].get_text(strip=True)) if len(cols) > 2 else None,
                    status=IPOStatus.FILED.value,
                    sector=self._classify_sector(company_name),
                    industry=self._classify_industry(company_name),
                    # Source attribution
                    source="sebi.gov.in",
                    source_reference="https://www.sebi.gov.in/sebiweb/home/list/3/4/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/P/0?type=3&category=4",
                    source_updated_at=datetime.utcnow(),
                    collector_version="1.0.0",
                    data_quality_score=0.75,  # Good - official regulator source
                )
                ipos.append(ipo)
            except Exception:
                continue
        return ipos

    @staticmethod
    def _classify_sector(name: str) -> Sector:
        """Classify sector based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['tech', 'software', 'system', 'digital', 'data', 'cloud', 'cyber', 'ai', 'it ', 'information']):
            return Sector.INFORMATION_TECHNOLOGY
        
        # Healthcare
        if any(kw in name_lower for kw in ['pharma', 'biotech', 'health', 'medical', 'hospital', 'diagnostic', 'drug', 'medicine', 'life science']):
            return Sector.HEALTH_CARE
        
        # Financial
        if any(kw in name_lower for kw in ['bank', 'finance', 'capital', 'investment', 'insurance', 'credit', 'loan', 'fintech', 'payment', 'wealth']):
            return Sector.FINANCIALS
        
        # Consumer Discretionary
        if any(kw in name_lower for kw in ['retail', 'consumer', 'fashion', 'apparel', 'footwear', 'jewel', 'auto', 'vehicle', 'travel', 'hotel', 'restaurant', 'food service']):
            return Sector.CONSUMER_DISCRETIONARY
        
        # Consumer Staples
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'grocery', 'fmcg', 'personal care', 'household']):
            return Sector.CONSUMER_STAPLES
        
        # Industrials
        if any(kw in name_lower for kw in ['engineering', 'manufacturing', 'industrial', 'construction', 'infrastructure', 'logistics', 'transport', 'cargo', 'shipping', 'transmission', 'power', 'energy', 'electrical', 'mechanical', 'machinery']):
            return Sector.INDUSTRIALS
        
        # Materials
        if any(kw in name_lower for kw in ['chemical', 'cement', 'steel', 'metal', 'mining', 'mineral', 'aluminium', 'copper', 'zinc', 'paper', 'packaging']):
            return Sector.MATERIALS
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum', 'refinery', 'solar', 'renewable', 'wind', 'hydro']):
            return Sector.ENERGY
        
        # Real Estate
        if any(kw in name_lower for kw in ['realty', 'real estate', 'property', 'developer', 'construction', 'housing', 'infra']):
            return Sector.REAL_ESTATE
        
        # Utilities
        if any(kw in name_lower for kw in ['utility', 'electric', 'power', 'water', 'gas distribution']):
            return Sector.UTILITIES
        
        # Communication Services
        if any(kw in name_lower for kw in ['telecom', 'communication', 'media', 'broadcast', 'entertainment', 'gaming']):
            return Sector.COMMUNICATION_SERVICES
        
        return Sector.UNCLASSIFIED

    @staticmethod
    def _classify_industry(name: str) -> Industry:
        """Classify industry based on company name keywords."""
        name_lower = name.lower()
        
        # Technology
        if any(kw in name_lower for kw in ['software', 'saas', 'platform', 'app', 'digital', 'analytics', 'cloud', 'cyber']):
            return Industry.SOFTWARE
        if any(kw in name_lower for kw in ['semi', 'chip', 'electronics', 'hardware']):
            return Industry.SEMICONDUCTORS
        if any(kw in name_lower for kw in ['it service', 'consulting', 'outsourcing']):
            return Industry.IT_SERVICES
        if any(kw in name_lower for kw in ['ai', 'machine learning', 'ml ', 'artificial intelligence']):
            return Industry.AI_ML
        if any(kw in name_lower for kw in ['cyber', 'security']):
            return Industry.CYBERSECURITY
        if any(kw in name_lower for kw in ['fintech', 'payment', 'wallet']):
            return Industry.FINTECH
        if any(kw in name_lower for kw in ['ecommerce', 'e-commerce', 'marketplace', 'online']):
            return Industry.ECOMMERCE
        
        # Healthcare
        if any(kw in name_lower for kw in ['biotech', 'biotechnology']):
            return Industry.BIOTECH
        if any(kw in name_lower for kw in ['pharma', 'pharmaceutical']):
            return Industry.PHARMACEUTICALS
        if any(kw in name_lower for kw in ['medical device', 'diagnostic']):
            return Industry.MEDICAL_DEVICES
        if any(kw in name_lower for kw in ['hospital', 'healthcare service']):
            return Industry.HEALTHCARE_SERVICES
        if any(kw in name_lower for kw in ['diagnostic']):
            return Industry.DIAGNOSTICS
        
        # Financial
        if any(kw in name_lower for kw in ['bank']):
            return Industry.BANKING
        if any(kw in name_lower for kw in ['insurance']):
            return Industry.INSURANCE
        if any(kw in name_lower for kw in ['asset management', 'mutual fund', 'wealth']):
            return Industry.ASSET_MANAGEMENT
        if any(kw in name_lower for kw in ['payment', 'gateway']):
            return Industry.PAYMENTS
        
        # Consumer
        if any(kw in name_lower for kw in ['retail', 'store', 'shop']):
            return Industry.RETAIL
        if any(kw in name_lower for kw in ['food', 'beverage', 'dairy', 'restaurant']):
            return Industry.FOOD_BEVERAGE
        if any(kw in name_lower for kw in ['apparel', 'garment', 'textile', 'fashion']):
            return Industry.APPAREL
        if any(kw in name_lower for kw in ['auto', 'vehicle', 'car', 'ev ', 'electric vehicle']):
            return Industry.AUTOMOTIVE
        
        # Industrial
        if any(kw in name_lower for kw in ['aerospace', 'aviation', 'defense']):
            return Industry.AEROSPACE
        if any(kw in name_lower for kw in ['manufacturing', 'factory', 'production']):
            return Industry.MANUFACTURING
        if any(kw in name_lower for kw in ['logistics', 'supply chain', 'transport', 'cargo', 'shipping']):
            return Industry.LOGISTICS
        if any(kw in name_lower for kw in ['construction', 'infra', 'infrastructure']):
            return Industry.CONSTRUCTION
        
        # Energy
        if any(kw in name_lower for kw in ['oil', 'gas', 'petroleum']):
            return Industry.OIL_GAS
        if any(kw in name_lower for kw in ['solar', 'wind', 'renewable', 'green energy']):
            return Industry.RENEWABLE_ENERGY
        
        # Materials
        if any(kw in name_lower for kw in ['chemical']):
            return Industry.CHEMICALS
        if any(kw in name_lower for kw in ['metal', 'mining', 'steel', 'aluminium', 'copper']):
            return Industry.METALS_MINING
        
        return Industry.OTHER

    def _extract_symbol(self, name: str) -> str:
        """Extract symbol from company name."""
        import re
        match = re.search(r"\(([A-Z0-9]{1,20})\)", name)
        if match:
            return match.group(1)
        # Generate from name
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        return cleaned[:20] if cleaned else "UNKNOWN"

    def _parse_date(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    def _parse_sebi_data(self, data: Any) -> List[IPODetails]:
        """Parse SEBI JSON API response."""
        ipos = []
        if isinstance(data, dict):
            data = data.get("data", [])
        elif not isinstance(data, list):
            return ipos
        
        for item in data:
            try:
                company_name = item.get("companyName") or item.get("issuerName") or ""
                symbol = (item.get("symbol") or item.get("scripCode") or "").upper()
                if not symbol:
                    symbol = self._extract_symbol(company_name)
                
                ipo = IPODetails(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=Exchange.NSE,
                    expected_date=self._parse_date(item.get("openDate")),
                    listed_date=self._parse_date(item.get("listingDate")),
                    status=IPOStatus.FILED.value,
                    price_range=self._parse_price_range(item),
                    shares_offered=self._parse_int(item.get("issueSize")),
                    sector=self._classify_sector(company_name),
                    industry=self._classify_industry(company_name),
                    # Source attribution
                    source="sebi.gov.in",
                    source_reference="https://www.sebi.gov.in/sebiweb/home/HomeController/getAllIPODetails",
                    source_updated_at=datetime.utcnow(),
                    collector_version="1.0.0",
                    data_quality_score=0.8,  # High - official regulator data
                )
                ipos.append(ipo)
            except Exception:
                continue
        return ipos

    def _parse_price_range(self, item: Dict[str, Any]) -> Optional[PriceRange]:
        low = item.get("priceLow") or item.get("floorPrice")
        high = item.get("priceHigh") or item.get("capPrice")
        if low is not None and high is not None:
            try:
                return PriceRange(
                    low=Money(Decimal(str(low)), "INR"),
                    high=Money(Decimal(str(high)), "INR"),
                )
            except Exception:
                pass
        return None

    def _parse_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value).replace(",", "").strip())
        except Exception:
            return None

    async def fetch_recent(self, days: int = 30) -> ProviderResult[List[IPODetails]]:
        """Fetch recently listed IPOs from SEBI."""
        # SEBI doesn't have a simple "recent" endpoint
        return await self.fetch_upcoming(lookahead_days=days)

    async def fetch_by_symbol(self, symbol: str) -> ProviderResult[Optional[IPODetails]]:
        result = await self.fetch_upcoming(lookahead_days=365)
        if result.success and result.data:
            for ipo in result.data:
                if ipo.symbol.upper() == symbol.upper():
                    return ProviderResult(success=True, data=ipo)
        return ProviderResult(success=False, error=f"Not found: {symbol}")