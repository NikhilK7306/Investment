"""External services package."""

from app.infrastructure.external_services.providers import (
    BaseProvider,
    ProviderConfig,
    ProviderResult,
    ProviderRegistry,
    ProviderStatus,
    IPODataProvider,
    FinancialDataProvider,
    NewsDataProvider,
    get_provider_registry,
)

from app.infrastructure.external_services.indian_providers import (
    InvestorGainProvider,
    NSEIndiaProvider,
    BSEIndiaProvider,
    SEBIProvider,
)

from app.infrastructure.external_services.international_providers import (
    NASDAQProvider,
    NYSEProvider,
    SECEdgarProvider,
    RenaissanceCapitalProvider,
)

from app.infrastructure.external_services.indian_financial_providers import (
    FMPIndianProvider,
    AlphaVantageIndianProvider,
    DRHPDocumentProvider,
)

from app.infrastructure.external_services.news_providers import (
    NewsAPIProvider,
    AlphaVantageNewsProvider,
    RSSNewsProvider,
    FinancialModelingPrepProvider,
)

from app.infrastructure.external_services.social_providers import (
    RedditProvider,
    TwitterProvider,
    StockTwitsProvider,
)

__all__ = [
    # Base
    "BaseProvider",
    "ProviderConfig",
    "ProviderResult",
    "ProviderRegistry",
    "ProviderStatus",
    "IPODataProvider",
    "FinancialDataProvider",
    "NewsDataProvider",
    "get_provider_registry",
    # Indian IPO providers
    "InvestorGainProvider",
    "NSEIndiaProvider",
    "BSEIndiaProvider",
    "SEBIProvider",
    # Indian Financial providers
    "FMPIndianProvider",
    "AlphaVantageIndianProvider",
    "DRHPDocumentProvider",
    # International providers
    "NASDAQProvider",
    "NYSEProvider",
    "SECEdgarProvider",
    "RenaissanceCapitalProvider",
    # News providers
    "NewsAPIProvider",
    "AlphaVantageNewsProvider",
    "RSSNewsProvider",
    "FinancialModelingPrepProvider",
    # Social providers
    "RedditProvider",
    "TwitterProvider",
    "StockTwitsProvider",
]