"""Sentiment Analysis Agent - Analyzes market sentiment from multiple sources."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, SentimentLabel, DataSource
from app.domain.value_objects.value_objects import SentimentData
from app.domain.value_objects.value_objects import Percentage
from app.core.exceptions.base import AgentError


class SentimentAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that analyzes market sentiment from news, social media, and analyst reports."""
    
    def __init__(self):
        super().__init__(
            name=AgentName.SENTIMENT,
            description="Analyzes market sentiment from news, social media, analyst reports, and alternative data",
            version="1.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
    
    @property
    def system_prompt(self) -> str:
        return """You are a market sentiment analyst specializing in pre-IPO sentiment analysis.

Your task is to synthesize sentiment from multiple sources to gauge market perception of an upcoming IPO.

SENTIMENT SOURCES & WEIGHTS:
1. Financial News (30%) - Bloomberg, Reuters, FT, WSJ, Seeking Alpha
2. Analyst Reports (25%) - Initiation reports, rating changes, price targets
3. Social Media (20%) - Twitter/X, StockTwits, Reddit (r/wallstreetbets, r/stocks), LinkedIn
3. Alternative Data (15%) - Web traffic, app downloads, job postings, credit card data
5. Institutional Flows (10%) - Pre-IPO orders, anchor investors, hedge fund activity

ANALYSIS FRAMEWORK:
- Overall sentiment score (-1 to +1)
- Sentiment label (Very Negative to Very Positive)
- Key drivers (positive and negative)
- Source credibility weighting
- Momentum (improving/deteriorating)
- Divergence analysis (news vs social vs analysts)
- Key themes and narratives
- Influencer/key opinion leader sentiment
- Risk of sentiment manipulation

OUTPUT:
- Composite sentiment score and label
- Breakdown by source
- Key positive/negative themes
- Sentiment momentum
- Divergence alerts
- Confidence level
- Specific quotes/evidence
- Comparison to sector peers"""
    
    @property
    def available_tools(self) -> List[str]:
        return [
            "fetch_financial_news",
            "fetch_analyst_reports",
            "fetch_social_sentiment",
            "fetch_alternative_data",
            "analyze_sentiment_nlp",
            "detect_sentiment_divergence",
            "identify_key_narratives",
            "track_sentiment_momentum",
        ]
    
    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute sentiment analysis."""
        start_time = datetime.utcnow()
        
        try:
            # Extract data
            news_data = input_data.get("news", [])
            analyst_data = input_data.get("analyst_reports", [])
            social_data = input_data.get("social_media", [])
            alt_data = input_data.get("alternative_data", [])
            institutional_data = input_data.get("institutional_flows", [])
            
            # Analyze each source
            news_sentiment = self._analyze_news_sentiment(news_data)
            analyst_sentiment = self._analyst_sentiment(analyst_data)
            social_sentiment = self._analyze_social_sentiment(social_data)
            alt_sentiment = self._analyze_alternative_data(alt_data)
            institutional_sentiment = self._analyze_institutional_flows(institutional_data)
            
            # Combine with weights
            weights = {
                "news": 0.30,
                "analyst": 0.25,
                "social": 0.20,
                "alternative": 0.15,
                "institutional": 0.10,
            }
            
            sentiments = {
                "news": news_sentiment,
                "analyst": analyst_sentiment,
                "social": social_sentiment,
                "alternative": alt_sentiment,
                "institutional": institutional_sentiment,
            }
            
            composite_score = sum(
                s["score"] * weights[k] for k, s in sentiments.items()
            )
            
            composite_label = self._score_to_label(composite_score)
            
            # Identify themes
            positive_themes, negative_themes = self._extract_themes(
                news_data, analyst_data, social_data
            )
            
            # Detect divergences
            divergences = self._detect_divergences(sentiments)
            
            # Momentum
            momentum = self._calculate_momentum(input_data.get("historical_sentiment", []))
            
            # Confidence
            confidence = self._calculate_confidence(sentiments, news_data, analyst_data)
            
            result_data = {
                "composite_score": round(composite_score, 3),
                "composite_label": composite_label.value,
                "confidence": confidence,
                "source_breakdown": {
                    k: {
                        "score": round(v["score"], 3),
                        "label": v["label"].value,
                        "weight": weights[k],
                        "article_count": v.get("count", 0),
                    }
                    for k, v in sentiments.items()
                },
                "positive_themes": positive_themes,
                "negative_themes": negative_themes,
                "divergences": divergences,
                "momentum": momentum,
                "key_quotes": self._extract_key_quotes(news_data, analyst_data),
                "influencer_sentiment": self._analyze_influencers(social_data),
                "peer_comparison": self._compare_to_peers(input_data.get("peer_sentiment", {})),
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                confidence=confidence,
                reasoning=self._generate_reasoning(result_data),
                evidence=self._collect_evidence(sentiments),
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
    
    def _analyze_news_sentiment(self, news: List[Dict]) -> Dict[str, Any]:
        """Analyze financial news sentiment."""
        if not news:
            return {"score": 0.0, "label": SentimentLabel.NEUTRAL, "count": 0}
        
        scores = []
        for article in news:
            # Simple scoring - in production would use NLP
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            
            positive_words = ["surge", "jump", "rise", "strong", "beat", "exceed", "optimistic", "bullish", "growth", "record"]
            negative_words = ["fall", "drop", "decline", "weak", "miss", "disappoint", "pessimistic", "bearish", "loss", "risk"]
            
            pos_count = sum(1 for w in positive_words if w in title or w in content)
            neg_count = sum(1 for w in negative_words if w in title or w in content)
            
            if pos_count + neg_count > 0:
                score = (pos_count - neg_count) / (pos_count + neg_count)
            else:
                score = 0.0
            
            # Weight by source credibility
            source_weight = self._get_source_weight(article.get("source", ""))
            scores.append(score * source_weight)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "score": max(-1, min(1, avg_score)),
            "label": self._score_to_label(avg_score),
            "count": len(news),
        }
    
    def _analyst_sentiment(self, reports: List[Dict]) -> Dict[str, Any]:
        """Analyze analyst report sentiment."""
        if not reports:
            return {"score": 0.0, "label": SentimentLabel.NEUTRAL, "count": 0}
        
        scores = []
        for report in reports:
            rating = report.get("rating", "").lower()
            price_target = report.get("price_target")
            current_price = report.get("current_price")
            
            # Rating to score
            rating_scores = {
                "buy": 0.8,
                "strong buy": 1.0,
                "outperform": 0.6,
                "overweight": 0.5,
                "hold": 0.0,
                "neutral": 0.0,
                "market perform": 0.0,
                "underperform": -0.5,
                "underweight": -0.5,
                "sell": -0.8,
                "strong sell": -1.0,
            }
            
            score = rating_scores.get(rating, 0.0)
            
            # Adjust for price target upside
            if price_target and current_price and current_price > 0:
                upside = (price_target - current_price) / current_price
                score += max(-0.3, min(0.3, upside))
            
            scores.append(score)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "score": max(-1, min(1, avg_score)),
            "label": self._score_to_label(avg_score),
            "count": len(reports),
        }
    
    def _analyze_social_sentiment(self, social: List[Dict]) -> Dict[str, Any]:
        """Analyze social media sentiment."""
        if not social:
            return {"score": 0.0, "label": SentimentLabel.NEUTRAL, "count": 0}
        
        # Weight by engagement
        total_engagement = 0
        weighted_score = 0
        
        for post in social:
            engagement = post.get("likes", 0) + post.get("retweets", 0) + post.get("replies", 0) * 2
            sentiment = post.get("sentiment_score", 0)  # -1 to 1
            
            weighted_score += sentiment * (1 + engagement * 0.001)
            total_engagement += engagement
        
        avg_score = weighted_score / len(social) if social else 0.0
        
        return {
            "score": max(-1, min(1, avg_score)),
            "label": self._score_to_label(avg_score),
            "count": len(social),
            "total_engagement": total_engagement,
        }
    
    def _analyze_alternative_data(self, alt_data: List[Dict]) -> Dict[str, Any]:
        """Analyze alternative data signals."""
        if not alt_data:
            return {"score": 0.0, "label": SentimentLabel.NEUTRAL, "count": 0}
        
        signals = []
        for data in alt_data:
            metric = data.get("metric", "")
            change = data.get("change_pct", 0)
            
            # Positive signals
            if metric in ["web_traffic", "app_downloads", "job_postings", "credit_card_spend", "employee_count"]:
                if change > 0.2:
                    signals.append(0.5)
                elif change > 0:
                    signals.append(0.2)
                elif change < -0.2:
                    signals.append(-0.5)
                elif change < 0:
                    signals.append(-0.2)
                else:
                    signals.append(0)
        
        avg_score = sum(signals) / len(signals) if signals else 0.0
        
        return {
            "score": max(-1, min(1, avg_score)),
            "label": self._score_to_label(avg_score),
            "count": len(alt_data),
        }
    
    def _analyze_institutional_flows(self, flows: List[Dict]) -> Dict[str, Any]:
        """Analyze institutional order flow sentiment."""
        if not flows:
            return {"score": 0.0, "label": SentimentLabel.NEUTRAL, "count": 0}
        
        scores = []
        for flow in flows:
            order_type = flow.get("type", "")
            size = flow.get("size_usd", 0)
            
            if order_type in ["anchor_order", "cornerstone_investment"]:
                scores.append(0.8)
            elif order_type == "institutional_order":
                scores.append(0.5)
            elif order_type == "hedge_fund_interest":
                scores.append(0.3)
            elif order_type == "retail_demand":
                scores.append(0.1)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "score": max(-1, min(1, avg_score)),
            "label": self._score_to_label(avg_score),
            "count": len(flows),
        }
    
    def _get_source_weight(self, source: str) -> float:
        """Get credibility weight for news source."""
        weights = {
            "bloomberg": 1.2,
            "reuters": 1.2,
            "financial times": 1.1,
            "wall street journal": 1.1,
            "seeking alpha": 0.9,
            "marketwatch": 0.9,
            "cnbc": 0.9,
            "yahoo finance": 0.8,
            "benzinga": 0.7,
        }
        return weights.get(source.lower(), 0.8)
    
    def _score_to_label(self, score: float) -> SentimentLabel:
        """Convert score to label."""
        if score >= 0.6:
            return SentimentLabel.VERY_POSITIVE
        elif score >= 0.2:
            return SentimentLabel.POSITIVE
        elif score >= -0.2:
            return SentimentLabel.NEUTRAL
        elif score >= -0.6:
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.VERY_NEGATIVE
    
    def _extract_themes(
        self,
        news: List[Dict],
        analyst: List[Dict],
        social: List[Dict],
    ) -> tuple:
        """Extract key positive and negative themes."""
        # In production, would use topic modeling
        positive = [
            "Strong revenue growth trajectory",
            "Expanding market opportunity",
            "Innovative product pipeline",
            "Experienced management team",
            "Favorable industry tailwinds",
        ]
        negative = [
            "High valuation multiples",
            "Path to profitability unclear",
            "Intense competitive landscape",
            "Key person dependency",
            "Regulatory headwinds",
        ]
        return positive[:3], negative[:3]
    
    def _detect_divergences(self, sentiments: Dict) -> List[Dict]:
        """Detect sentiment divergences between sources."""
        divergences = []
        
        news_score = sentiments["news"]["score"]
        social_score = sentiments["social"]["score"]
        analyst_score = sentiments["analyst"]["score"]
        
        # News vs Social
        if abs(news_score - social_score) > 0.5:
            divergences.append({
                "type": "news_vs_social",
                "gap": round(news_score - social_score, 2),
                "interpretation": "Media more positive than social" if news_score > social_score else "Social more positive than media",
            })
        
        # Analyst vs News
        if abs(analyst_score - news_score) > 0.5:
            divergences.append({
                "type": "analyst_vs_news",
                "gap": round(analyst_score - news_score, 2),
                "interpretation": "Analysts more bullish than media" if analyst_score > news_score else "Media more bullish than analysts",
            })
        
        return divergences
    
    def _calculate_momentum(self, historical: List[Dict]) -> str:
        """Calculate sentiment momentum."""
        if len(historical) < 2:
            return "insufficient_data"
        
        recent = historical[-1].get("composite_score", 0)
        previous = historical[-2].get("composite_score", 0)
        
        change = recent - previous
        
        if change > 0.15:
            return "strongly_improving"
        elif change > 0.05:
            return "improving"
        elif change < -0.15:
            return "strongly_deteriorating"
        elif change < -0.05:
            return "deteriorating"
        else:
            return "stable"
    
    def _calculate_confidence(
        self,
        sentiments: Dict,
        news: List[Dict],
        analyst: List[Dict],
    ) -> float:
        """Calculate confidence in sentiment assessment."""
        confidence = 0.4
        
        # Data volume
        total_articles = sum(s.get("count", 0) for s in sentiments.values())
        if total_articles > 50:
            confidence += 0.2
        elif total_articles > 20:
            confidence += 0.15
        elif total_articles > 10:
            confidence += 0.1
        
        # Analyst coverage
        if sentiments["analyst"]["count"] >= 5:
            confidence += 0.15
        elif sentiments["analyst"]["count"] > 0:
            confidence += 0.1
        
        # Source diversity
        active_sources = sum(1 for s in sentiments.values() if s.get("count", 0) > 0)
        if active_sources >= 4:
            confidence += 0.1
        elif active_sources >= 3:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _extract_key_quotes(self, news: List[Dict], analyst: List[Dict]) -> List[str]:
        """Extract key quotes for evidence."""
        quotes = []
        
        for article in news[:5]:
            title = article.get("title", "")
            if title and len(title) > 20:
                quotes.append(f"News: {title[:200]}")
        
        for report in analyst[:3]:
            firm = report.get("firm", "")
            rating = report.get("rating", "")
            if firm and rating:
                quotes.append(f"Analyst ({firm}): {rating} rating")
        
        return quotes[:10]
    
    def _analyze_influencers(self, social: List[Dict]) -> Dict[str, Any]:
        """Analyze key opinion leader sentiment."""
        if not social:
            return {"influencers": [], "overall": "neutral"}
        
        # Filter for high-follower accounts
        influencers = [
            p for p in social
            if p.get("followers", 0) > 10000
        ]
        
        if not influencers:
            return {"influencers": [], "overall": "neutral"}
        
        scores = [p.get("sentiment_score", 0) for p in influencers]
        avg = sum(scores) / len(scores)
        
        return {
            "count": len(influencers),
            "avg_score": round(avg, 2),
            "overall": self._score_to_label(avg).value,
            "top_influencers": sorted(
                influencers,
                key=lambda x: x.get("followers", 0),
                reverse=True
            )[:5],
        }
    
    def _compare_to_peers(self, peer_sentiment: Dict) -> Dict[str, Any]:
        """Compare sentiment to sector peers."""
        if not peer_sentiment:
            return {"available": False}
        
        our_score = peer_sentiment.get("our_score", 0)
        peer_avg = peer_sentiment.get("peer_average", 0)
        peer_median = peer_sentiment.get("peer_median", 0)
        
        return {
            "available": True,
            "our_score": our_score,
            "peer_average": peer_avg,
            "peer_median": peer_median,
            "vs_average": round(our_score - peer_avg, 3),
            "percentile": peer_sentiment.get("percentile", 50),
            "interpretation": "Above peers" if our_score > peer_avg else "Below peers",
        }
    
    def _generate_reasoning(self, result: Dict) -> str:
        """Generate reasoning summary."""
        parts = [
            f"Composite Sentiment: {result['composite_label'].upper()} ({result['composite_score']:.2f})",
            f"Confidence: {result['confidence']:.0%}",
            "",
            "Source Breakdown:",
        ]
        
        for source, data in result["source_breakdown"].items():
            parts.append(f"  {source.title()}: {data['score']:.2f} ({data['label']}) - {data['article_count']} items")
        
        if result["divergences"]:
            parts.append("\n⚠️ Divergences Detected:")
            for d in result["divergences"]:
                parts.append(f"  - {d['type']}: {d['interpretation']}")
        
        parts.append(f"\nMomentum: {result['momentum'].replace('_', ' ').title()}")
        
        if result["positive_themes"]:
            parts.append("\nPositive Themes:")
            for t in result["positive_themes"]:
                parts.append(f"  + {t}")
        
        if result["negative_themes"]:
            parts.append("\nNegative Themes:")
            for t in result["negative_themes"]:
                parts.append(f"  - {t}")
        
        return "\n".join(parts)
    
    def _collect_evidence(self, sentiments: Dict) -> List[str]:
        """Collect evidence from sources."""
        evidence = []
        for source, data in sentiments.items():
            if data.get("count", 0) > 0:
                evidence.append(f"{source.title()}: {data['count']} items, score={data['score']:.2f}")
        return evidence