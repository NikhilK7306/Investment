"""Chat Agent - Handles conversational queries about IPOs using RAG and LLM."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import AgentName, AgentStatus
from app.core.exceptions.base import AgentError
from app.infrastructure.ai_models import LLMProviderFactory, LLMConfig, LLMProviderType


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # user, assistant, system
    content: str
    agent: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = {}


class ChatContext(BaseModel):
    """Chat context with relevant IPO data."""
    ipo_symbol: Optional[str] = None
    ipo_name: Optional[str] = None
    analysis_summary: Dict[str, Any] = {}
    financial_data: Dict[str, Any] = {}
    market_data: Dict[str, Any] = {}
    risk_data: Dict[str, Any] = {}
    sentiment_data: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Chat agent response."""
    message: str
    agent_used: Optional[str] = None
    sources: List[Dict[str, str]] = []
    confidence: float = Field(ge=0, le=1)
    follow_up_questions: List[str] = []


class ChatAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that handles conversational queries about IPOs using RAG and LLM."""

    def __init__(self):
        super().__init__(
            name=AgentName.COLLECTION,  # Reuse collection agent name for now
            description="Handles conversational queries about IPOs using RAG and LLM",
            version="2.0.0",
            max_retries=2,
            timeout_seconds=120,
        )
        self._llm_provider = None
        self._conversation_history: List[ChatMessage] = []

    @property
    def system_prompt(self) -> str:
        return """You are an IPO Intelligence Assistant helping users understand IPO analysis.

Your role is to answer questions about IPOs using the provided context and analysis data.

GUIDELINES:
- Use ONLY the provided context and analysis data
- If information is not available in the context, say "I don't have that information in the current analysis"
- Distinguish clearly between VERIFIED FACTS (from analysis data) and YOUR INTERPRETATION
- Cite specific sections of the analysis when answering
- Be concise but thorough
- If asked about future predictions, include confidence levels and uncertainty
- Never present AI analysis as guaranteed outcomes

CAPABILITIES:
- Explain analysis results (scores, recommendations, risks)
- Compare IPOs
- Explain financial metrics
- Discuss market conditions
- Explain risks and catalysts
- Discuss valuation methodology

LIMITATIONS:
- Cannot access real-time data beyond provided context
- Cannot make personalized investment advice
- Cannot guarantee outcomes"""

    @property
    def available_tools(self) -> List[str]:
        return [
            "search_analysis",
            "get_financial_data",
            "get_risk_factors",
            "get_market_data",
            "compare_ipos",
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
            user_message = input_data.get("message", "")
            ipo_symbol = input_data.get("ipo_symbol", context.ipo_symbol)
            conversation_history = input_data.get("conversation_history", [])

            if not user_message:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.FAILED,
                    error="No message provided",
                    error_type="MISSING_MESSAGE",
                )

            provider = self._get_llm_provider()
            await provider.initialize()

            # Build context from available data
            chat_context = self._build_context(ipo_symbol, input_data.get("analysis_data", {}))

            # Create prompt with conversation history
            prompt = self._create_chat_prompt(
                user_message, chat_context, conversation_history
            )

            # Call LLM
            response = await provider.complete(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,
                max_tokens=2000,
            )

            # Parse response
            if isinstance(response.content, str):
                try:
                    response_data = json.loads(response.content)
                except json.JSONDecodeError:
                    response_data = {"message": response.content, "agent_used": None, "sources": [], "confidence": 0.8}
            else:
                response_data = response.content

            # Ensure required fields
            chat_response = ChatResponse(**response_data)

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=chat_response.model_dump(),
                confidence=chat_response.confidence,
                reasoning=chat_response.message,
                evidence=chat_response.sources,
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

    def _build_context(self, ipo_symbol: Optional[str], analysis_data: Dict) -> ChatContext:
        """Build chat context from analysis data."""
        context = ChatContext(
            ipo_symbol=ipo_symbol,
            ipo_name=analysis_data.get("company_name", analysis_data.get("ipo_details", {}).get("company_name")),
            analysis_summary=analysis_data.get("overall_analysis", {}),
            financial_data=analysis_data.get("financial_analysis", {}),
            market_data=analysis_data.get("market_analysis", {}),
            risk_data=analysis_data.get("risk_analysis", {}),
            sentiment_data=analysis_data.get("sentiment_analysis", {}),
        )
        return context

    def _create_chat_prompt(
        self,
        user_message: str,
        context: ChatContext,
        history: List[Dict],
    ) -> str:
        """Create the chat prompt with context and history."""
        
        # Build context summary
        context_parts = []
        
        if context.ipo_symbol:
            context_parts.append(f"IPO: {context.ipo_symbol}")
        if context.ipo_name:
            context_parts.append(f"Company: {context.ipo_name}")
        
        # Analysis summary
        overall = context.analysis_summary
        if overall:
            context_parts.append(f"""
OVERALL ANALYSIS:
- Score: {overall.get('overall_score', 'N/A')}/100
- Recommendation: {overall.get('recommendation', 'N/A')}
- Risk Level: {overall.get('risk_level', 'N/A')}
- Time Horizon: {overall.get('time_horizon', 'N/A')}
- Confidence: {overall.get('confidence', 'N/A')}
- Bull Case: {overall.get('bull_case', 'N/A')[:200]}...
- Bear Case: {overall.get('bear_case', 'N/A')[:200]}...
""")
        
        # Financial highlights
        financial = context.financial_data
        if financial:
            context_parts.append(f"""
FINANCIAL HIGHLIGHTS:
{json.dumps(financial.get('key_metrics', {}), indent=2)}
""")
        
        # Risk highlights
        risk = context.risk_data
        if risk:
            top_risks = risk.get('top_risks', [])[:3]
            if top_risks:
                context_parts.append(f"""
TOP RISKS:
{json.dumps(top_risks, indent=2)}
""")
        
        # Sentiment
        sentiment = context.sentiment_data
        if sentiment:
            context_parts.append(f"""
SENTIMENT:
- Score: {sentiment.get('composite_score', 'N/A')}
- Label: {sentiment.get('composite_label', 'N/A')}
- Confidence: {sentiment.get('confidence', 'N/A')}
""")
        
        # Conversation history
        history_parts = []
        for msg in history[-6:]:  # Last 6 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            agent = msg.get("agent", "")
            if agent:
                history_parts.append(f"[{role} via {agent}]: {content}")
            else:
                history_parts.append(f"[{role}]: {content}")
        
        prompt = f"""CONTEXT:
{' '.join(context_parts)}

CONVERSATION HISTORY:
{' '.join(history_parts) if history_parts else 'No previous messages'}

USER QUESTION: {user_message}

ANSWER THE USER'S QUESTION USING ONLY THE CONTEXT PROVIDED. If information is not available, say so. Distinguish between verified facts and interpretation. Cite specific analysis sections when possible."""
        return prompt

    def _extract_json(self, content: str) -> Dict:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass
        # Return simple response if JSON parsing fails
        return {"message": content, "agent_used": None, "sources": [], "confidence": 0.8}