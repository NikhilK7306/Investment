"""Social media data providers for sentiment analysis."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.infrastructure.external_services.providers import (
    ProviderConfig,
    ProviderResult,
)


class RedditProvider:
    """Provider for Reddit sentiment data."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        config = ProviderConfig(
            name="reddit",
            base_url="https://oauth.reddit.com",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=60 if self.client_id else 0,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token for Reddit API."""
        if not self.client_id or not self.client_secret:
            return None
        
        if self._access_token and self._token_expires and self._token_expires > datetime.utcnow():
            return self._access_token
        
        try:
            auth = httpx.BasicAuth(self.client_id, self.client_secret)
            data = {"grant_type": "client_credentials"}
            headers = {"User-Agent": "IPO Intelligence Agent/1.0"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    data=data,
                    headers=headers,
                )
                
                if response.status_code != 200:
                    return None
                
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                return self._access_token
                
        except Exception:
            return None

    async def _check_health(self) -> None:
        token = await self._get_access_token()
        if not token:
            raise Exception("Reddit authentication failed")
        
        client = await self._get_client()
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/r/wallstreetbets/hot", params={"limit": 1}, headers=headers, timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"Reddit API returned {response.status_code}")

    async def fetch_posts(
        self,
        subreddit: str = "wallstreetbets",
        query: str = "",
        limit: int = 25,
        timeframe: str = "day",
    ) -> ProviderResult[List[Dict[str, Any]]]:
        token = await self._get_access_token()
        if not token:
            return ProviderResult(
                success=False,
                error="Reddit credentials not configured or authentication failed",
                error_type="AUTH_ERROR",
            )
        
        try:
            client = await self._get_client()
            headers = {"Authorization": f"Bearer {token}"}
            
            if query:
                endpoint = f"/r/{subreddit}/search"
                params = {
                    "q": query,
                    "limit": min(limit, 100),
                    "restrict_sr": "true",
                    "sort": "relevance",
                    "t": timeframe,
                }
            else:
                endpoint = f"/r/{subreddit}/hot"
                params = {"limit": min(limit, 100)}
            
            response = await client.get(endpoint, params=params, headers=headers, timeout=30.0)
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"Reddit API returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="reddit.com",
                )
            
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            
            results = []
            for post in posts[:limit]:
                post_data = post.get("data", {})
                results.append({
                    "id": post_data.get("id"),
                    "title": post_data.get("title", ""),
                    "selftext": post_data.get("selftext", ""),
                    "author": post_data.get("author", ""),
                    "score": post_data.get("score", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc"),
                    "url": post_data.get("url", ""),
                    "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                    "subreddit": post_data.get("subreddit", ""),
                    "flair": post_data.get("link_flair_text", ""),
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="reddit.com",
                source_reference=f"https://reddit.com/r/{subreddit}",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="reddit.com",
            )

    async def fetch_comments(
        self,
        post_id: str,
        limit: int = 50,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        token = await self._get_access_token()
        if not token:
            return ProviderResult(success=False, error="Not authenticated")
        
        try:
            client = await self._get_client()
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.get(
                f"/comments/{post_id}",
                params={"limit": limit, "depth": 3},
                headers=headers,
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(success=False, error=f"HTTP {response.status_code}")
            
            data = response.json()
            # Second element contains comments
            if len(data) < 2:
                return ProviderResult(success=True, data=[])
            
            comments_data = data[1].get("data", {}).get("children", [])
            
            results = []
            for comment in comments_data[:limit]:
                if comment.get("kind") != "t1":
                    continue
                c = comment.get("data", {})
                results.append({
                    "id": c.get("id"),
                    "body": c.get("body", ""),
                    "author": c.get("author", ""),
                    "score": c.get("score", 0),
                    "created_utc": c.get("created_utc"),
                    "permalink": f"https://reddit.com{c.get('permalink', '')}",
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="reddit.com",
            )
            
        except Exception as e:
            return ProviderResult(success=False, error=str(e))


class TwitterProvider:
    """Provider for Twitter/X sentiment data (requires Twitter API v2)."""

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        config = ProviderConfig(
            name="twitter",
            base_url="https://api.twitter.com/2",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=300 if self.bearer_token else 0,  # Elevated access
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        if not self.bearer_token:
            raise Exception("Twitter bearer token not configured")
        client = await self._get_client()
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        response = await client.get(
            "/tweets/search/recent",
            params={"query": "IPO", "max_results": 10},
            headers=headers,
            timeout=10.0,
        )
        if response.status_code not in (200, 401, 404):
            raise Exception(f"Twitter API returned {response.status_code}")

    async def fetch_tweets(
        self,
        query: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        if not self.bearer_token:
            return ProviderResult(
                success=False,
                error="Twitter bearer token not configured",
                error_type="MISSING_API_KEY",
            )
        
        try:
            client = await self._get_client()
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            
            params = {
                "query": query,
                "max_results": min(limit, 100),
                "tweet.fields": "created_at,author_id,public_metrics,lang",
                "expansions": "author_id",
                "user.fields": "username,verified",
            }
            
            if start_time:
                params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            response = await client.get(
                "/tweets/search/recent",
                params=params,
                headers=headers,
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"Twitter API returned {response.status_code}: {response.text}",
                    error_type="HTTP_ERROR",
                    source="twitter.com",
                )
            
            data = response.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            results = []
            for tweet in tweets[:limit]:
                author = users.get(tweet.get("author_id", ""), {})
                metrics = tweet.get("public_metrics", {})
                
                results.append({
                    "id": tweet.get("id"),
                    "text": tweet.get("text", ""),
                    "author_id": tweet.get("author_id", ""),
                    "author_username": author.get("username", ""),
                    "author_verified": author.get("verified", False),
                    "created_at": tweet.get("created_at"),
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "like_count": metrics.get("like_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "lang": tweet.get("lang", ""),
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="twitter.com",
                source_reference="https://api.twitter.com/2/tweets/search/recent",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="twitter.com",
            )


class StockTwitsProvider:
    """Provider for StockTwits sentiment data."""

    def __init__(self):
        config = ProviderConfig(
            name="stocktwits",
            base_url="https://api.stocktwits.com/api/2",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=200,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/streams/symbol/AAPL.json", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"StockTwits API returned {response.status_code}")

    async def fetch_messages(
        self,
        symbol: str,
        limit: int = 30,
    ) -> ProviderResult[List[Dict[str, Any]]]:
        try:
            client = await self._get_client()
            response = await client.get(
                f"/streams/symbol/{symbol.upper()}.json",
                params={"limit": min(limit, 30)},
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"StockTwits returned {response.status_code}",
                    error_type="HTTP_ERROR",
                    source="stocktwits.com",
                )
            
            data = response.json()
            messages = data.get("messages", [])
            
            results = []
            for msg in messages[:limit]:
                user = msg.get("user", {})
                sentiment = msg.get("entities", {}).get("sentiment", {})
                
                results.append({
                    "id": msg.get("id"),
                    "body": msg.get("body", ""),
                    "created_at": msg.get("created_at"),
                    "user_id": user.get("id"),
                    "username": user.get("username", ""),
                    "followers": user.get("followers", 0),
                    "sentiment": sentiment.get("basic", "neutral"),
                    "sentiment_score": 1 if sentiment.get("basic") == "bullish" else (-1 if sentiment.get("basic") == "bearish" else 0),
                    "likes": msg.get("likes", {}).get("total", 0),
                })
            
            return ProviderResult(
                success=True,
                data=results,
                source="stocktwits.com",
                source_reference=f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="stocktwits.com",
            )