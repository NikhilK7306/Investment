"""News and sentiment data providers."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.infrastructure.external_services.providers import (
    NewsDataProvider,
    ProviderConfig,
    ProviderResult,
)


class NewsAPIProvider(NewsDataProvider):
    """Provider for news data from NewsAPI.org."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        config = ProviderConfig(
            name="newsapi",
            base_url="https://newsapi.org/v2",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=100 if self.api_key else 0,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        if not self.api_key:
            raise Exception("NewsAPI key not configured")
        client = await self._get_client()
        response = await client.get(
            "/top-headlines",
            params={"category": "business", "pageSize": 1},
            timeout=10.0,
        )
        if response.status_code not in (200, 401, 404):
            raise Exception(f"NewsAPI returned {response.status_code}")

    async def fetch_news(
        self,
        query: str,
        limit: int = 20,
        from_date: Optional[datetime] = None,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="NewsAPI key not configured",
                error_type="MISSING_API_KEY",
            )
        
        try:
            client = await self._get_client()
            params = {
                "q": query,
                "pageSize": min(limit, 100),
                "language": "en",
                "sortBy": "publishedAt",
            }
            
            if from_date:
                params["from"] = from_date.strftime("%Y-%m-%d")
            
            response = await client.get(
                "/everything",
                params=params,
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"NewsAPI returned {response.status_code}: {response.text}",
                    error_type="HTTP_ERROR",
                    source="newsapi.org",
                )
            
            data = response.json()
            articles = data.get("articles", [])
            
            results = []
            for article in articles:
                results.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "published_at": article.get("publishedAt", ""),
                    "url_to_image": article.get("urlToImage", ""),
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="newsapi.org",
                source_reference="https://newsapi.org/v2/everything",
                metadata={"total_results": data.get("totalResults", 0)},
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="newsapi.org",
            )


class AlphaVantageNewsProvider(NewsDataProvider):
    """Provider for news/sentiment data from Alpha Vantage."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        config = ProviderConfig(
            name="alphavantage_news",
            base_url="https://www.alphavantage.co",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=5 if self.api_key else 0,  # Free tier: 5/min
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        if not self.api_key:
            raise Exception("Alpha Vantage API key not configured")
        client = await self._get_client()
        response = await client.get(
            "/query",
            params={"function": "NEWS_SENTIMENT", "tickers": "AAPL", "apikey": self.api_key},
            timeout=10.0,
        )
        if response.status_code not in (200, 404):
            raise Exception(f"Alpha Vantage returned {response.status_code}")

    async def fetch_news(
        self,
        query: str,
        limit: int = 20,
        from_date: Optional[datetime] = None,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="Alpha Vantage API key not configured",
                error_type="MISSING_API_KEY",
            )
        
        try:
            client = await self._get_client()
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": query,
                "limit": min(limit, 50),
                "apikey": self.api_key,
            }
            
            if from_date:
                params["time_from"] = from_date.strftime("%Y%m%dT%H%M")
            
            response = await client.get("/query", params=params, timeout=30.0)
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"Alpha Vantage returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="alphavantage.co",
                )
            
            data = response.json()
            feed = data.get("feed", [])
            
            results = []
            for item in feed[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", ""),
                    "author": item.get("author", ""),
                    "published_at": item.get("time_published", ""),
                    "sentiment_score": item.get("overall_sentiment_score"),
                    "sentiment_label": item.get("overall_sentiment_label"),
                    "ticker_sentiment": item.get("ticker_sentiment", []),
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="alphavantage.co",
                source_reference="https://www.alphavantage.co/query?function=NEWS_SENTIMENT",
                metadata={"items_returned": len(results)},
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="alphavantage.co",
            )


class RSSNewsProvider(NewsDataProvider):
    """Provider for news from RSS feeds."""

    def __init__(self, feed_urls: Optional[List[str]] = None):
        self.feed_urls = feed_urls or [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://www.ft.com/rss/home/us",
            "https://feeds.wsj.com/wsj/xml/WSJcom.xml",
        ]
        config = ProviderConfig(
            name="rss_news",
            base_url="",  # Direct URLs
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=30,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        # Check first feed
        client = await self._get_client()
        response = await client.get(self.feed_urls[0], timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"RSS feed returned {response.status_code}")

    async def fetch_news(
        self,
        query: str,
        limit: int = 20,
        from_date: Optional[datetime] = None,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        try:
            import feedparser
            
            all_entries = []
            
            for feed_url in self.feed_urls:
                try:
                    client = await self._get_client()
                    response = await client.get(feed_url, timeout=30.0)
                    
                    if response.status_code != 200:
                        continue
                    
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries[:limit]:
                        published = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        
                        if from_date and published and published < from_date:
                            continue
                        
                        # Simple query matching in title/summary
                        title = entry.get("title", "").lower()
                        summary = entry.get("summary", "").lower()
                        query_lower = query.lower()
                        
                        if query_lower not in title and query_lower not in summary:
                            continue
                        
                        all_entries.append({
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", ""),
                            "url": entry.get("link", ""),
                            "source": feed.feed.get("title", "RSS"),
                            "published_at": entry.get("published", ""),
                            "tags": [tag.term for tag in entry.get("tags", [])],
                        })
                        
                except Exception:
                    continue
            
            # Sort by date descending
            all_entries.sort(
                key=lambda x: x.get("published_at", ""),
                reverse=True,
            )
            
            return ProviderResult(
                success=True,
                data=all_entries[:limit],
                source="rss_feeds",
                source_reference="; ".join(self.feed_urls),
                metadata={"feeds_processed": len(self.feed_urls)},
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="rss_feeds",
            )


class FinancialModelingPrepProvider(NewsDataProvider):
    """Provider for financial news from Financial Modeling Prep."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        config = ProviderConfig(
            name="fmp_news",
            base_url="https://financialmodelingprep.com/api/v3",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=30 if self.api_key else 0,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        if not self.api_key:
            raise Exception("FMP API key not configured")
        client = await self._get_client()
        response = await client.get(
            "/stock_news",
            params={"tickers": "AAPL", "limit": 1, "apikey": self.api_key},
            timeout=10.0,
        )
        if response.status_code not in (200, 404):
            raise Exception(f"FMP returned {response.status_code}")

    async def fetch_news(
        self,
        query: str,
        limit: int = 20,
        from_date: Optional[datetime] = None,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="FMP API key not configured",
                error_type="MISSING_API_KEY",
            )
        
        try:
            client = await self._get_client()
            params = {
                "tickers": query,
                "limit": min(limit, 100),
                "apikey": self.api_key,
            }
            
            response = await client.get("/stock_news", params=params, timeout=30.0)
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"FMP returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="financialmodelingprep.com",
                )
            
            data = response.json()
            
            results = []
            for item in data[:limit]:
                published = item.get("publishedDate")
                if from_date and published:
                    try:
                        pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        if pub_date < from_date:
                            continue
                    except Exception:
                        pass
                
                results.append({
                    "title": item.get("title", ""),
                    "summary": item.get("text", "")[:500],
                    "url": item.get("url", ""),
                    "source": item.get("site", ""),
                    "author": item.get("author", ""),
                    "published_at": published,
                    "symbols": item.get("symbols", []),
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="financialmodelingprep.com",
                source_reference="https://financialmodelingprep.com/api/v3/stock_news",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="financialmodelingprep.com",
            )