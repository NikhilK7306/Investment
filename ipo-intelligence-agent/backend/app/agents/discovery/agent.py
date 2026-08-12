"""Discovery Agent - finds upcoming IPOs from multiple sources."""

import asyncio
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from app.agents.base.agent import AgentContext, AgentResult, BaseAgent
from app.domain.enums.enums import AgentName, AgentStatus, Exchange, IPOStatus, Sector, Industry
from app.domain.value_objects.value_objects import IPODetails, PriceRange
from app.domain.value_objects.value_objects import Money, Percentage
from app.core.exceptions.base import AgentError
from app.infrastructure.external_services import get_provider_registry


class DiscoveryAgent(BaseAgent[Dict[str, Any], List[IPODetails]]):
    """Agent that discovers upcoming IPOs from multiple sources using provider registry."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.DISCOVERY,
            description="Discovers upcoming IPOs from exchanges, SEC filings, and financial news",
            version="2.0.0",
            max_retries=3,
            timeout_seconds=180,
        )
        self._seen_symbols: Set[str] = set()
    
    @property
    def system_prompt(self) -> str:
        return """You are an IPO Discovery Agent. Your job is to identify and extract information about upcoming IPOs from various data sources.

You have access to multiple data providers for Indian and International IPOs. When analyzing sources, look for:
1. Company name and ticker symbol
2. Exchange (NASDAQ, NYSE, NSE, BSE, etc.)
3. Expected IPO date
4. Price range (if available)
5. Shares offered
6. Industry/sector
7. Underwriters
8. Use of proceeds

Return structured data for each IPO found. Be thorough but avoid duplicates.
Handle missing data gracefully using NOT_ANNOUNCED, NOT_AVAILABLE, NOT_APPLICABLE states."""
    
    @property
    def available_tools(self) -> List[str]:
        return [
            "fetch_indian_ipos",
            "fetch_international_ipos",
            "fetch_all_ipos",
            "validate_ipo_data",
            "check_duplicate",
        ]
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[List[IPODetails]]:
        """Execute IPO discovery using provider registry."""
        start_time = datetime.utcnow()
        discovered_ipos = []
        errors = []
        
        # Get configuration
        lookahead_days = input_data.get("lookahead_days", 90)
        sources = input_data.get("sources", ["nasdaq", "nyse", "sec", "renaissance", "investorgain"])
        min_market_cap = input_data.get("min_market_cap", 0)
        region = input_data.get("region", "all")  # "india", "international", "all"
        
        # Get provider registry
        registry = get_provider_registry()
        
        # Fetch from IPO providers with fallback
        ipo_providers = registry.get_ipo_providers()
        
        # Filter providers by region if specified
        if region == "india":
            ipo_providers = [p for p in ipo_providers if p.name in ("investorgain", "nse_india", "bse_india", "sebi")]
        elif region == "international":
            ipo_providers = [p for p in ipo_providers if p.name in ("nasdaq", "nyse", "sec_edgar", "renaissance")]
        
        # Execute discovery with fallback
        for provider in ipo_providers:
            if not provider.config.enabled:
                continue
                
            try:
                result = await provider.fetch_upcoming(
                    lookahead_days=lookahead_days,
                )
                
                if result.success and result.data:
                    discovered_ipos.extend(result.data)
                elif result.error:
                    errors.append(f"{provider.name}: {result.error}")
                    
            except Exception as e:
                errors.append(f"{provider.name}: {str(e)}")
        
        # Deduplicate
        unique_ipos = self._deduplicate_ipos(discovered_ipos)
        
        # Filter by minimum market cap if specified
        if min_market_cap > 0:
            unique_ipos = [
                ipo for ipo in unique_ipos
                if ipo.expected_raise and ipo.expected_raise.amount >= min_market_cap
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
            reasoning=f"Discovered {len(enriched_ipos)} unique IPOs from {len(ipo_providers)} providers",
            evidence=[f"Provider: {p.name}" for p in ipo_providers] + errors,
            metadata={
                "providers_used": [p.name for p in ipo_providers],
                "total_found": len(discovered_ipos),
                "after_dedup": len(unique_ipos),
                "after_filter": len(enriched_ipos),
                "errors": errors,
            },
            duration_ms=duration_ms,
        )
    
    async def _enrich_ipos(self, ipos: List[IPODetails]) -> List[IPODetails]:
        """Enrich IPOs with additional data from collection providers."""
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
    
    @staticmethod
    def _to_symbol(name: str) -> str:
        """Convert an IPO name to an uppercase alphanumeric symbol."""
        cleaned = re.sub(r"[^A-Z0-9]+", "", name.upper())
        if len(cleaned) > 20:
            cleaned = cleaned[:20]
        return cleaned

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """Parse an ISO date string (e.g. 2026-08-12) or US M/D/YYYY (e.g. 8/06/2026)."""
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
                "CR": Decimal("10000000"), "CRORE": Decimal("10000000"),
                "L": Decimal("100000"), "LAKH": Decimal("100000"),
                "K": Decimal("1000"),
            }.get(unit, Decimal("1"))
            return Money(number * multiplier, "INR")
        except Exception:
            return None

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