"""Base provider abstractions for external data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from enum import Enum

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from app.domain.enums.enums import DataSource
from app.domain.value_objects.value_objects import IPODetails, Money, PriceRange
from app.core.exceptions.base import ExternalServiceError, RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ProviderStatus(str, Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderResult(Generic[T]):
    """Result from a provider operation."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    source: str = ""
    source_reference: str = ""
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for a data provider."""
    name: str
    base_url: str
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Dict[str, str]] = None
    enabled: bool = True


class BaseProvider(ABC, Generic[T]):
    """Abstract base class for data providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._status = ProviderStatus.UNKNOWN
        self._last_error: Optional[str] = None
        self._request_count = 0
        self._error_count = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> ProviderStatus:
        return self._status

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=self.config.headers,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        client = await self._get_client()
        self._request_count += 1

        try:
            response = await client.request(method, path, params=params, json=json)
            
            if response.status_code == 429:
                self._error_count += 1
                self._status = ProviderStatus.DEGRADED
                raise RateLimitError(
                    self.config.name,
                    retry_after=int(response.headers.get("Retry-After", "60"))
                )
            
            response.raise_for_status()
            self._status = ProviderStatus.HEALTHY
            return response
            
        except httpx.HTTPStatusError as e:
            self._error_count += 1
            if e.response.status_code >= 500:
                self._status = ProviderStatus.DEGRADED
            raise ExternalServiceError(
                self.config.name,
                f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.TimeoutException:
            self._error_count += 1
            self._status = ProviderStatus.DEGRADED
            raise
        except httpx.NetworkError:
            self._error_count += 1
            self._status = ProviderStatus.UNHEALTHY
            raise

    async def health_check(self) -> ProviderStatus:
        """Check provider health."""
        try:
            await self._check_health()
            self._status = ProviderStatus.HEALTHY
        except Exception as e:
            self._last_error = str(e)
            self._status = ProviderStatus.UNHEALTHY
        return self._status

    @abstractmethod
    async def _check_health(self) -> None:
        """Provider-specific health check."""
        pass

    @abstractmethod
    async def fetch(self, **kwargs) -> ProviderResult[T]:
        """Fetch data from provider."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "name": self.config.name,
            "status": self._status.value,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
        }


class IPODataProvider(BaseProvider[List[IPODetails]]):
    """Abstract base for IPO data providers."""

    @abstractmethod
    async def fetch_upcoming(
        self,
        lookahead_days: int = 90,
        exchange: Optional[str] = None,
    ) -> ProviderResult[List[IPODetails]]:
        """Fetch upcoming IPOs."""
        pass

    @abstractmethod
    async def fetch_recent(
        self,
        days: int = 30,
    ) -> ProviderResult[List[IPODetails]]:
        """Fetch recently listed IPOs."""
        pass

    @abstractmethod
    async def fetch_by_symbol(
        self,
        symbol: str,
    ) -> ProviderResult[Optional[IPODetails]]:
        """Fetch specific IPO by symbol."""
        pass

    async def fetch(self, **kwargs) -> ProviderResult[List[IPODetails]]:
        """Default fetch implementation - delegates to fetch_upcoming."""
        lookahead_days = kwargs.get("lookahead_days", 90)
        exchange = kwargs.get("exchange")
        return await self.fetch_upcoming(lookahead_days=lookahead_days, exchange=exchange)


class FinancialDataProvider(BaseProvider[Dict[str, Any]]):
    """Abstract base for financial data providers."""

    @abstractmethod
    async def fetch_financials(
        self,
        symbol: str,
        periods: int = 8,
    ) -> ProviderResult[Dict[str, Any]]:
        """Fetch financial statements."""
        pass

    @abstractmethod
    async def fetch_company_profile(
        self,
        symbol: str,
    ) -> ProviderResult[Dict[str, Any]]:
        """Fetch company profile."""
        pass

    @abstractmethod
    async def fetch_drhp_financials(
        self,
        symbol: str,
        company_name: str,
        ipo_details: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult[Dict[str, Any]]:
        """Fetch financial statements from DRHP/RHP documents for pre-IPO companies."""
        pass

    async def fetch(self, **kwargs) -> ProviderResult[Dict[str, Any]]:
        """Default fetch implementation - delegates to fetch_financials."""
        symbol = kwargs.get("symbol", "")
        periods = kwargs.get("periods", 8)
        return await self.fetch_financials(symbol=symbol, periods=periods)


class NewsDataProvider(BaseProvider[List[Dict[str, Any]]]):
    """Abstract base for news data providers."""

    @abstractmethod
    async def fetch_news(
        self,
        query: str,
        limit: int = 20,
        from_date: Optional[datetime] = None,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        """Fetch news articles."""
        pass

    async def fetch(self, **kwargs) -> ProviderResult[List[Dict[str, Any]]]:
        """Default fetch implementation - delegates to fetch_news."""
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 20)
        from_date = kwargs.get("from_date")
        return await self.fetch_news(query=query, limit=limit, from_date=from_date)


class ProviderRegistry:
    """Registry for managing data providers."""

    def __init__(self):
        self._ipo_providers: List[IPODataProvider] = []
        self._financial_providers: List[FinancialDataProvider] = []
        self._news_providers: List[NewsDataProvider] = []
        self._all_providers: List[BaseProvider] = []

    def register_ipo_provider(self, provider: IPODataProvider) -> None:
        self._ipo_providers.append(provider)
        self._all_providers.append(provider)

    def register_financial_provider(self, provider: FinancialDataProvider) -> None:
        self._financial_providers.append(provider)
        self._all_providers.append(provider)

    def register_news_provider(self, provider: NewsDataProvider) -> None:
        self._news_providers.append(provider)
        self._all_providers.append(provider)

    def get_ipo_providers(self) -> List[IPODataProvider]:
        return [p for p in self._ipo_providers if p.config.enabled]

    def get_financial_providers(self) -> List[FinancialDataProvider]:
        return [p for p in self._financial_providers if p.config.enabled]

    def get_news_providers(self) -> List[NewsDataProvider]:
        return [p for p in self._news_providers if p.config.enabled]

    async def fetch_with_fallback(
        self,
        providers: List[BaseProvider],
        operation: str,
        **kwargs,
    ) -> ProviderResult:
        """Try providers in order until one succeeds."""
        last_error = None

        for provider in providers:
            try:
                logger.info(f"Trying provider: {provider.name}")
                method = getattr(provider, operation)
                result = await method(**kwargs)

                if result.success:
                    logger.info(f"Provider {provider.name} succeeded")
                    return result
                else:
                    last_error = result.error
                    logger.warning(f"Provider {provider.name} failed: {result.error}")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {provider.name} raised exception: {e}")

        return ProviderResult(
            success=False,
            error=f"All providers failed. Last error: {last_error}",
            error_type="ALL_PROVIDERS_FAILED",
        )

    async def health_check_all(self) -> Dict[str, ProviderStatus]:
        """Check health of all providers."""
        results = {}
        for provider in self._all_providers:
            results[provider.name] = await provider.health_check()
        return results

    async def close_all(self) -> None:
        """Close all provider clients."""
        for provider in self._all_providers:
            await provider.close()


# Global registry instance
_provider_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get global provider registry."""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
    return _provider_registry