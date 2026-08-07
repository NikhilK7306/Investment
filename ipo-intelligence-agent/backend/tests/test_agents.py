import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents.discovery.agent import DiscoveryAgent
from app.agents.fundamental.agent import FundamentalAnalysisAgent
from app.agents.market.agent import MarketAnalysisAgent
from app.agents.risk.agent import RiskAnalysisAgent
from app.agents.sentiment.agent import SentimentAnalysisAgent
from app.agents.decision.agent import DecisionSupportAgent
from app.agents.base import AgentContext, AgentStatus


class TestDiscoveryAgent:
    """Tests for Discovery Agent."""
    
    @pytest.fixture
    def agent(self):
        return DiscoveryAgent()
    
    @pytest.fixture
    def context(self):
        return AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-analysis-id",
        )
    
    @pytest.mark.asyncio
    async def test_execute_returns_structured_result(self, agent, context):
        """Test that execute returns proper AgentResult."""
        with patch.object(agent, '_fetch_nasdaq_ipos', new_callable=AsyncMock) as mock_nasdaq, \
             patch.object(agent, '_fetch_nyse_ipos', new_callable=AsyncMock) as mock_nyse, \
             patch.object(agent, '_fetch_sec_filings', new_callable=AsyncMock) as mock_sec:
            
            mock_nasdaq.return_value = []
            mock_nyse.return_value = []
            mock_sec.return_value = []
            
            result = await agent.execute(context, {"sources": ["nasdaq", "nyse"]})
            
            assert result.agent_name == "discovery"
            assert result.status == AgentStatus.COMPLETED
            assert "discovered" in result.reasoning.lower()
    
    def test_system_prompt_contains_key_instructions(self, agent):
        prompt = agent.system_prompt
        assert "IPO Discovery Agent" in prompt
        assert "ticker symbol" in prompt.lower()
        assert "price range" in prompt.lower()


class TestFundamentalAnalysisAgent:
    """Tests for Fundamental Analysis Agent."""
    
    @pytest.fixture
    def agent(self):
        return FundamentalAnalysisAgent()
    
    @pytest.fixture
    def context(self):
        return AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-analysis-id",
        )
    
    @pytest.mark.asyncio
    async def test_execute_with_financial_data(self, agent, context):
        """Test analysis with valid financial data."""
        financials = [{
            "revenue": 100000000,
            "gross_profit": 75000000,
            "operating_income": 20000000,
            "net_income": 15000000,
            "ebitda": 25000000,
            "free_cash_flow": 18000000,
            "total_assets": 200000000,
            "total_equity": 120000000,
            "total_debt": 30000000,
            "cash_and_equivalents": 50000000,
            "gross_margin": 0.75,
            "operating_margin": 0.20,
            "net_margin": 0.15,
            "revenue_growth_yoy": 0.25,
        }]
        
        input_data = {
            "financials": financials,
            "company_profile": {},
            "public_comps": [],
        }
        
        result = await agent.execute(context, input_data)
        
        assert result.agent_name == "fundamental"
        assert result.status == AgentStatus.COMPLETED
        assert 0 <= result.data["overall_score"] <= 100
        assert 0 <= result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_execute_without_financial_data(self, agent, context):
        """Test handling of missing financial data."""
        input_data = {"financials": []}
        
        result = await agent.execute(context, input_data)
        
        assert result.status == AgentStatus.FAILED
        assert result.error_type == "MISSING_DATA"
    
    def test_red_flag_detection(self, agent):
        """Test red flag identification."""
        from app.domain.value_objects.value_objects import FinancialMetrics, Money, Percentage, Ratio
        
        metrics = FinancialMetrics(
            revenue=Money(Decimal("100000000"), "USD"),
            revenue_growth_yoy=Percentage.from_decimal(-0.10),  # Negative growth
            gross_margin=Percentage.from_decimal(0.25),  # Low margin
            free_cash_flow=Money(Decimal("-5000000"), "USD"),  # Negative FCF
            total_debt=Money(Decimal("150000000"), "USD"),
            cash_and_equivalents=Money(Decimal("10000000"), "USD"),
            current_ratio=Ratio(Decimal("0.8"), "Current Ratio"),
        )
        
        financials = [{
            "revenue": 100000000,
            "gross_margin": 0.25,
            "free_cash_flow": -5000000,
            "total_debt": 150000000,
            "cash_and_equivalents": 10000000,
            "current_ratio": 0.8,
        }]
        
        red_flags = agent._identify_red_flags(metrics, financials)
        
        assert len(red_flags) >= 3
        assert any("Negative free cash flow" in f for f in red_flags)
        assert any("Current ratio below 1.0" in f for f in red_flags)


class TestMarketAnalysisAgent:
    """Tests for Market Analysis Agent."""
    
    @pytest.fixture
    def agent(self):
        return MarketAnalysisAgent()
    
    @pytest.fixture
    def context(self):
        return AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-analysis-id",
        )
    
    @pytest.mark.asyncio
    async def test_execute_with_company_profile(self, agent, context):
        """Test market analysis with company profile."""
        company_profile = {
            "sector": "technology",
            "industry": "software",
            "business_model": "platform",
            "target_markets": ["global"],
            "competitive_advantages": ["network effects", "high switching costs"],
            "tam": 50000000000,
        }
        
        input_data = {
            "company_profile": company_profile,
            "industry_data": {"market_cagr": 0.20, "tailwinds": ["AI adoption"]},
            "competitors": [
                {"name": "Comp1", "type": "direct", "public": True},
                {"name": "Comp2", "type": "direct", "public": True},
            ],
            "financials": [{"revenue": 100000000}],
        }
        
        result = await agent.execute(context, input_data)
        
        assert result.agent_name == "market"
        assert result.status == AgentStatus.COMPLETED
        assert "tam_analysis" in result.data
        assert "competitive_analysis" in result.data
    
    def test_tam_estimation(self, agent):
        """Test TAM estimation logic."""
        tam = agent._estimate_tam(
            sector="technology",
            industry="software",
            target_markets=["global"],
            industry_data={"market_cagr": 0.15}
        )
        
        assert tam["tam_usd"] > 0
        assert tam["cagr"] == 0.15
        assert "methodology" in tam
    
    def test_sam_calculation(self, agent):
        """Test SAM calculation."""
        tam_analysis = {"tam_usd": 500000000000}
        company_profile = {"business_model": "platform"}
        
        sam = agent._estimate_sam(tam_analysis, company_profile, "platform")
        
        assert sam["sam_usd"] > 0
        assert sam["sam_tam_ratio"] == 0.25  # Platform gets 25%
    
    def test_som_calculation(self, agent):
        """Test SOM calculation."""
        sam_analysis = {"sam_usd": 125000000000}
        company_profile = {}
        financials = [{"revenue": 50000000}]
        
        som = agent._estimate_som(sam_analysis, company_profile, financials)
        
        assert som["som_usd"] > 0
        assert som["projected_market_share"] > 0


class TestRiskAnalysisAgent:
    """Tests for Risk Analysis Agent."""
    
    @pytest.fixture
    def agent(self):
        return RiskAnalysisAgent()
    
    @pytest.fixture
    def context(self):
        return AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-analysis-id",
        )
    
    @pytest.mark.asyncio
    async def test_financial_risk_detection(self, agent):
        """Test detection of financial risks."""
        latest = {
            "revenue_concentration": {"top_customer_pct": 0.4, "top_5_customers_pct": 0.65},
            "gross_margin": 0.45,
            "total_debt": 1000000000,
            "ebitda": 150000000,
            "free_cash_flow": -20000000,
            "cash_and_equivalents": 100000000,
        }
        
        risks = agent._analyze_financial_risks(latest, [], {})
        
        assert len(risks) >= 3
        risk_categories = [r.category for r in risks]
        assert "Financial" in risk_categories
        
        # Check high debt/EBITDA risk
        debt_risk = next((r for r in risks if "High Leverage" in r.factor), None)
        assert debt_risk is not None
        assert debt_risk.severity.value in ["high", "very_high"]
    
    def test_overall_risk_level_calculation(self, agent):
        """Test overall risk level determination."""
        from app.domain.entities.entities import RiskFactor
        from app.domain.enums.enums import RiskLevel, Percentage
        
        # High risk factors
        risks = [
            RiskFactor("Financial", "Risk 1", RiskLevel.EXTREME, Percentage.from_decimal(0.9), Percentage.from_decimal(0.9), "Desc"),
            RiskFactor("Market", "Risk 2", RiskLevel.VERY_HIGH, Percentage.from_decimal(0.8), Percentage.from_decimal(0.8), "Desc"),
            RiskFactor("Operational", "Risk 3", RiskLevel.HIGH, Percentage.from_decimal(0.7), Percentage.from_decimal(0.7), "Desc"),
        ]
        
        overall = agent._determine_overall_risk(risks)
        assert overall in [RiskLevel.EXTREME, RiskLevel.VERY_HIGH]


class TestSentimentAnalysisAgent:
    """Tests for Sentiment Analysis Agent."""
    
    @pytest.fixture
    def agent(self):
        return SentimentAnalysisAgent()
    
    @pytest.fixture
    def context(self):
        return AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-analysis-id",
        )
    
    def test_news_sentiment_analysis(self, agent):
        """Test news sentiment scoring."""
        news = [
            {"title": "Company beats earnings estimates, stock surges", "source": "Bloomberg"},
            {"title": "Analyst upgrades rating to buy", "source": "Reuters"},
            {"title": "Revenue growth accelerates", "source": "Financial Times"},
        ]
        
        result = agent._analyze_news_sentiment(news)
        
        assert result["score"] > 0
        assert result["label"].value in ["positive", "very_positive"]
        assert result["count"] == 3
    
    def test_analyst_sentiment_analysis(self, agent):
        """Test analyst report sentiment."""
        reports = [
            {"rating": "Buy", "price_target": 25, "current_price": 20},
            {"rating": "Strong Buy", "price_target": 30, "current_price": 20},
            {"rating": "Hold", "price_target": 20, "current_price": 20},
        ]
        
        result = agent._analyst_sentiment(reports)
        
        assert result["score"] > 0
        assert result["label"].value in ["positive", "very_positive"]
    
    def test_social_sentiment_weighting(self, agent):
        """Test social media sentiment with engagement weighting."""
        social = [
            {"sentiment_score": 0.8, "likes": 1000, "retweets": 500, "replies": 100},
            {"sentiment_score": -0.5, "likes": 100, "retweets": 20, "replies": 50},
        ]
        
        result = agent._analyze_social_sentiment(social)
        
        # Positive post has higher engagement, should weight more
        assert result["score"] > -0.5
    
    def test_divergence_detection(self, agent):
        """Test sentiment divergence detection."""
        sentiments = {
            "news": {"score": 0.8},
            "social": {"score": -0.6},
            "analyst": {"score": 0.5},
        }
        
        divergences = agent._detect_divergences(sentiments)
        
        assert len(divergences) >= 1
        d = divergences[0]
        assert d["type"] == "news_vs_social"
        assert d["gap"] > 1.0


class TestDecisionSupportAgent:
    """Tests for Decision Support Agent."""
    
    @pytest.fixture
    def agent(self):
        return DecisionSupportAgent()
    
    @pytest.fixture
    def context(self):
        return AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-analysis-id",
        )
    
    @pytest.mark.asyncio
    async def test_recommendation_mapping(self, agent):
        """Test score to recommendation mapping."""
        test_cases = [
            (95, "AGGRESSIVE_BUY"),
            (80, "BUY"),
            (65, "ACCUMULATE"),
            (50, "HOLD"),
            (40, "WATCH"),
            (30, "REDUCE"),
            (20, "SELL"),
            (10, "AVOID"),
        ]
        
        for score, expected in test_cases:
            result = agent._score_to_recommendation(score)
            assert result.value == expected.lower()
    
    def test_time_horizon_determination(self, agent):
        """Test time horizon logic."""
        # High growth + good timing + low risk = long term
        horizon = agent._determine_time_horizon(
            fundamental={"growth_analysis": {"score": 80}},
            market={"trends_analysis": {"timing_assessment": "excellent"}},
            risk={"overall_risk_score": 30},
        )
        assert horizon.value == "long_term"
        
        # High risk = short term
        horizon = agent._determine_time_horizon(
            fundamental={"growth_analysis": {"score": 30}},
            market={"trends_analysis": {"timing_assessment": "challenging"}},
            risk={"overall_risk_score": 70},
        )
        assert horizon.value == "short_term"
    
    def test_position_sizing(self, agent):
        """Test position sizing logic."""
        from app.domain.enums.enums import RiskLevel, TimeHorizon
        
        # High confidence, low risk, long horizon = larger position
        pos = agent._calculate_position_guidance(
            score=85,
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            time_horizon=TimeHorizon.LONG_TERM,
        )
        
        assert pos["suggested_max_pct"] > 5
        assert pos["suggested_entry_pct"] == pos["suggested_max_pct"] * 0.5
        
        # Low confidence, high risk, short horizon = minimal position
        pos = agent._calculate_position_guidance(
            score=30,
            confidence=0.3,
            risk_level=RiskLevel.HIGH,
            time_horizon=TimeHorizon.SHORT_TERM,
        )
        
        assert pos["suggested_max_pct"] <= 2


class TestAgentOrchestrator:
    """Tests for Agent Orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        from app.agents.base.agent import AgentOrchestrator
        return AgentOrchestrator()
    
    def test_register_agent(self, orchestrator):
        from app.agents.base.agent import BaseAgent
        from app.domain.enums.enums import AgentName
        
        class MockAgent(BaseAgent):
            @property
            def system_prompt(self):
                return "Test"
            
            @property
            def available_tools(self):
                return []
            
            async def execute(self, context, input_data):
                pass
        
        agent = MockAgent(AgentName.FUNDAMENTAL, "Test Agent")
        orchestrator.register_agent(agent)
        
        assert orchestrator.get_agent(AgentName.FUNDAMENTAL) == agent
    
    def test_execution_order(self, orchestrator):
        from app.domain.enums.enums import AgentName
        
        orchestrator.set_execution_order([
            [AgentName.DISCOVERY, AgentName.COLLECTION],
            [AgentName.FUNDAMENTAL, AgentName.MARKET, AgentName.RISK],
            [AgentName.DECISION],
        ])
        
        assert len(orchestrator._execution_order) == 3
        assert orchestrator._execution_order[0] == [AgentName.DISCOVERY, AgentName.COLLECTION]


# Integration tests
class TestAgentIntegration:
    """Integration tests for agent workflows."""
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel agent execution."""
        from app.agents.base.agent import AgentOrchestrator, AgentContext
        from app.domain.enums.enums import AgentName
        
        orchestrator = AgentOrchestrator()
        
        # Register mock agents
        class MockAgent:
            def __init__(self, name):
                self.name = name
            
            @property
            def system_prompt(self):
                return "Test"
            
            @property
            def available_tools(self):
                return []
            
            async def execute(self, context, input_data):
                from app.agents.base.agent import AgentResult, AgentStatus
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.COMPLETED,
                    data={"result": f"output from {self.name.value}"},
                    confidence=0.9,
                )
            
            async def run_with_retry(self, context, input_data):
                return await self.execute(context, input_data)
        
        for agent_name in [AgentName.FUNDAMENTAL, AgentName.MARKET, AgentName.RISK, AgentName.SENTIMENT]:
            orchestrator.register_agent(MockAgent(agent_name))
        
        orchestrator.set_execution_order([
            [AgentName.FUNDAMENTAL, AgentName.MARKET, AgentName.RISK, AgentName.SENTIMENT],
        ])
        
        context = AgentContext(
            ipo_symbol="TEST",
            analysis_id="test-id",
        )
        
        results = await orchestrator.execute_workflow(context, {})
        
        assert len(results) == 4
        for name in [AgentName.FUNDAMENTAL, AgentName.MARKET, AgentName.RISK, AgentName.SENTIMENT]:
            assert name in results
            assert results[name].status.value == "completed"


# Performance benchmarks (optional)
class TestPerformance:
    """Performance benchmarks for agents."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_fundamental_agent_performance(self):
        """Benchmark fundamental analysis agent."""
        import time
        from app.agents.fundamental.agent import FundamentalAnalysisAgent
        
        agent = FundamentalAnalysisAgent()
        context = AgentContext(ipo_symbol="TEST", analysis_id="perf-test")
        
        financials = [{
            "revenue": 100000000,
            "gross_profit": 75000000,
            "operating_income": 20000000,
            "net_income": 15000000,
            "free_cash_flow": 18000000,
            "total_assets": 200000000,
            "total_equity": 120000000,
            "total_debt": 30000000,
            "cash_and_equivalents": 50000000,
            "gross_margin": 0.75,
            "operating_margin": 0.20,
            "net_margin": 0.15,
            "revenue_growth_yoy": 0.25,
        }]
        
        input_data = {
            "financials": financials,
            "company_profile": {},
            "public_comps": [],
        }
        
        start = time.time()
        result = await agent.execute(context, input_data)
        elapsed = time.time() - start
        
        assert result.status.value == "completed"
        assert elapsed < 5.0  # Should complete in under 5 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])