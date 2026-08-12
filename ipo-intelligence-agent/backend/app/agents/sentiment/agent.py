"""Sentiment Analysis Agent - Analyzes market sentiment using LLM."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus, SentimentLabel, DataSource
from app.domain.value_objects.value_objects import SentimentData, Percentage
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class SourceSentiment(BaseModel):
    """Sentiment from a single source."""
    source: str
    score: float = Field(ge=-1, le=1)
    label: str
    weight: float = Field(ge=0, le=1)
    article_count: int = 0
    details: List[str] = []


class SentimentAnalysisOutput(BaseModel):
    """Structured output for sentiment analysis."""
    composite_score: float = Field(ge=-1, le=1)
    composite_label: str
    confidence: float = Field(ge=0, le=1)
    source_breakdown: Dict[str, SourceSentiment]
    positive_themes: List[str]
    negative_themes: List[str]
    divergences: List[Dict[str, Any]]
    momentum: str
    key_quotes: List[str]
    influencer_sentiment: Dict[str, Any]
    peer_comparison: Dict[str, Any]
    reasoning: str
    confidence_score: float = Field(ge=0, le=1)


class SentimentAnalysisAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that analyzes market sentiment from multiple sources using LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.SENTIMENT,
            description="Analyzes market sentiment from news, social media, analyst reports using LLM",
            version="2.0.0",
            max_retries=2,
            timeout_seconds=180,
        )
        self._llm_provider = None

    @property
    def system_prompt(self) -> str:
        return """You are a market sentiment analyst specializing in pre-IPO sentiment analysis.

Your task is to synthesize sentiment from multiple sources to gauge market perception of an upcoming IPO.

SENTIMENT SOURCES & WEIGHTS:
1. Financial News (30%) - Bloomberg, Reuters, FT, WSJ, Seeking Alpha
2. Analyst Reports (25%) - Initiation reports, rating changes, price targets
3. Social Media (20%) - Twitter/X, StockTwits, Reddit (r/wallstreetbets, r/stocks), LinkedIn
4. Alternative Data (15%) - Web traffic, app downloads, job postings, credit card data
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
- Comparison to sector peers

CRITICAL: Use ONLY the supplied verified data. If information is unavailable, return null/Not Available. Do NOT infer or fabricate factual values. Distinguish clearly between verified facts and your analytical interpretation. If there is insufficient news/data for a source, explicitly state "Insufficient Data" for that source."""

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

    def _get_llm_provider(self):
        if self._llm_provider is None:
            self._llm_provider = LLMProviderFactory.create_from_env()
        return self._llm_provider

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        start_time = datetime.utcnow()

        try:
            news_data = input_data.get("news", [])
            analyst_data = input_data.get("analyst_reports", [])
            social_data = input_data.get("social_media", [])
            alt_data = input_data.get("alternative_data", [])
            institutional_data = input_data.get("institutional_flows", [])
            peer_sentiment = input_data.get("peer_sentiment", {})
            historical_sentiment = input_data.get("historical_sentiment", [])

            # Check if we have ANY sentiment data
            has_any_data = any([
                news_data,
                analyst_data,
                social_data,
                alt_data,
                institutional_data,
                peer_sentiment,
                historical_sentiment,
            ])

            if not has_any_data:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.INSUFFICIENT_DATA,
                    error="No sentiment data provided (news, analyst reports, social media, etc.)",
                    error_type="INSUFFICIENT_DATA",
                    data={"data_quality": "none", "reason": "No sentiment data sources available"},
                )

            provider = self._get_llm_provider()
            await provider.initialize()

            sentiment_summary = self._prepare_sentiment_summary(
                news_data, analyst_data, social_data, alt_data, 
                institutional_data, peer_sentiment, historical_sentiment
            )

            prompt = self._create_analysis_prompt(sentiment_summary)

            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=4000,
                response_model=SentimentAnalysisOutput,
            )

            if isinstance(response.content, str):
                try:
                    analysis_data = json.loads(response.content)
                except json.JSONDecodeError:
                    analysis_data = self._extract_json(response.content)
            else:
                analysis_data = response.content

            analysis = SentimentAnalysisOutput(**analysis_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=analysis.model_dump(),
                confidence=analysis.confidence_score,
                reasoning=analysis.reasoning,
                evidence=self._collect_evidence(sentiment_summary),
                duration_ms=duration,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
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

    def _prepare_sentiment_summary(
        self,
        news: List,
        analyst: List,
        social: List,
        alt: List,
        institutional: List,
        peer_sentiment: Dict,
        historical: List,
    ) -> Dict[str, Any]:
        """Prepare verified sentiment data for LLM."""
        
        def count_items(data: List) -> int:
            return len(data) if isinstance(data, list) else 0
        
        summary = {
            "news": {
                "count": count_items(news),
                "sample_titles": [n.get("title", "") for n in news[:5]] if news else [],
            },
            "analyst_reports": {
                "count": count_items(analyst),
                "sample": analyst[:5] if analyst else [],
            },
            "social_media": {
                "count": count_items(social),
                "sample": social[:5] if social else [],
            },
            "alternative_data": {
                "count": count_items(alt),
                "sample": alt[:5] if alt else [],
            },
            "institutional_flows": {
                "count": count_items(institutional),
                "sample": institutional[:5] if institutional else [],
            },
            "peer_sentiment": peer_sentiment,
            "historical_sentiment": historical[-5:] if historical else [],
        }
        return summary

    def _create_analysis_prompt(self, summary: Dict) -> str:
        """Create the analysis prompt for the LLM."""
        prompt = f"""Analyze the market sentiment for the IPO candidate using ONLY the verified data provided below.

NEWS DATA ({summary['news']['count']} articles):
{json.dumps(summary['news']['sample'], indent=2)}

ANALYST REPORTS ({summary['analyst_reports']['count']} reports):
{json.dumps(summary['analyst_reports']['sample'], indent=2)}

SOCIAL MEDIA ({summary['social_media']['count']} posts):
{json.dumps(summary['social_media']['sample'], indent=2)}

ALTERNATIVE DATA ({summary['alternative_data']['count']} signals):
{json.dumps(summary['alternative_data']['sample'], indent=2)}

INSTITUTIONAL FLOWS ({summary['institutional_flows']['count']} data points):
{json.dumps(summary['institutional_flows']['sample'], indent=2)}

PEER SENTIMENT COMPARISON:
{json.dumps(summary['peer_sentiment'], indent=2)}

HISTORICAL SENTIMENT (last 5 periods):
{json.dumps(summary['historical_sentiment'], indent=2)}

REMEMBER: Use ONLY the data above. If a count is 0, state "Insufficient Data" for that source. Do NOT infer or fabricate sentiment. Distinguish clearly between VERIFIED FACTS (from data above) and YOUR ANALYSIS/INTERPRETATION."""
        return prompt

    def _extract_json(self, content: str) -> Dict:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass
        raise ValueError("Could not extract valid JSON from response")

    def _collect_evidence(self, summary: Dict) -> List[str]:
        evidence = []
        for source in ["news", "analyst_reports", "social_media", "alternative_data", "institutional_flows"]:
            count = summary.get(source, {}).get("count", 0)
            if count > 0:
                evidence.append(f"{source}: {count} items")
        return evidence