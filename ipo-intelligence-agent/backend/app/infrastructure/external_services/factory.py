"""Factory for creating and configuring data providers."""

import os
from typing import Optional

from app.core.config.settings import get_settings
from app.infrastructure.external_services.providers import get_provider_registry
from app.infrastructure.external_services import (
    # Indian IPO
    InvestorGainProvider,
    NSEIndiaProvider,
    BSEIndiaProvider,
    SEBIProvider,
    # International IPO
    NASDAQProvider,
    NYSEProvider,
    SECEdgarProvider,
    RenaissanceCapitalProvider,
    # Indian Financial
    FMPIndianProvider,
    AlphaVantageIndianProvider,
    DRHPDocumentProvider,
    # News
    NewsAPIProvider,
    AlphaVantageNewsProvider,
    RSSNewsProvider,
    FinancialModelingPrepProvider,
)


def create_provider_registry() -> "ProviderRegistry":
    """Create and configure the global provider registry with all available providers."""
    from app.infrastructure.external_services.providers import ProviderRegistry
    
    registry = ProviderRegistry()
    settings = get_settings()
    
    # ============================================================
    # IPO Data Providers
    # ============================================================
    
    # Indian IPO Providers
    registry.register_ipo_provider(InvestorGainProvider())
    registry.register_ipo_provider(NSEIndiaProvider())
    registry.register_ipo_provider(BSEIndiaProvider())
    registry.register_ipo_provider(SEBIProvider())
    
    # International IPO Providers
    registry.register_ipo_provider(NASDAQProvider())
    registry.register_ipo_provider(NYSEProvider())
    registry.register_ipo_provider(SECEdgarProvider())
    registry.register_ipo_provider(RenaissanceCapitalProvider())
    
    # ============================================================
    # Financial Data Providers
    # ============================================================
    
    # Indian Financial Providers (with fallback chain)
    # FMP - Primary for NSE/BSE listed companies
    if settings.fmp_api_key or os.getenv("FMP_API_KEY"):
        registry.register_financial_provider(FMPIndianProvider())
    
    # Alpha Vantage - Fallback for Indian financials
    if settings.alpha_vantage_api_key or os.getenv("ALPHA_VANTAGE_API_KEY"):
        registry.register_financial_provider(AlphaVantageIndianProvider())
    
    # DRHP Document Provider - For pre-IPO companies (always enabled, no API key needed)
    registry.register_financial_provider(DRHPDocumentProvider())
    
    # ============================================================
    # News Providers
    # ============================================================
    
    # NewsAPI (requires NEWSAPI_KEY)
    if getattr(settings, "newsapi_key", None) or os.getenv("NEWSAPI_KEY"):
        registry.register_news_provider(NewsAPIProvider())
    
    # Alpha Vantage (requires ALPHA_VANTAGE_API_KEY)
    if settings.alpha_vantage_api_key or os.getenv("ALPHA_VANTAGE_API_KEY"):
        registry.register_news_provider(AlphaVantageNewsProvider())
    
    # RSS Feeds (free, no API key needed)
    registry.register_news_provider(RSSNewsProvider())
    
    # Financial Modeling Prep (requires FMP_API_KEY)
    if os.getenv("FMP_API_KEY"):
        registry.register_news_provider(FinancialModelingPrepProvider())
    
    # ============================================================
    # Social Providers
    # ============================================================
    
    # Social providers are not fully implemented yet
    # Reddit (requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)
    # if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
    #     registry.register_news_provider(RedditProvider())
    
    # Twitter (requires TWITTER_BEARER_TOKEN)
    # if os.getenv("TWITTER_BEARER_TOKEN"):
    #     registry.register_news_provider(TwitterProvider())
    
    # StockTwits (free, no API key needed) - needs base class fix
    # registry.register_news_provider(StockTwitsProvider())
    
    return registry


async def initialize_providers() -> "ProviderRegistry":
    """Initialize all providers and run health checks."""
    registry = create_provider_registry()
    
    # Run health checks in parallel
    health_results = await registry.health_check_all()
    
    # Log results
    import logging
    logger = logging.getLogger(__name__)
    for name, status in health_results.items():
        if status.value == "healthy":
            logger.info(f"Provider {name}: {status.value}")
        else:
            logger.warning(f"Provider {name}: {status.value}")
    
    return registry


async def shutdown_providers() -> None:
    """Shutdown all provider connections."""
    registry = get_provider_registry()
    await registry.close_all()