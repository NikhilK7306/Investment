"""Unit tests for domain entities."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.entities import (
    Company,
    FinancialStatement,
    IPO,
    AnalysisResult,
    OverallAnalysis,
    Report,
    Money,
    Prediction,
)
from app.domain.enums.enums import (
    IPOStatus,
    Exchange,
    Sector,
    Industry,
    RiskLevel,
    SentimentLabel,
    AnalysisStatus,
    AgentName,
    InvestmentStrategy,
    TimeHorizon,
)
from app.domain.value_objects.value_objects import Money as VOMoney, Percentage, Ratio


class TestMoney:
    """Tests for Money value object."""
    
    def test_creation(self):
        money = Money(Decimal("100.50"), "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"
    
    def test_addition(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("50"), "USD")
        result = m1 + m2
        assert result.amount == Decimal("150")
    
    def test_subtraction(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("30"), "USD")
        result = m1 - m2
        assert result.amount == Decimal("70")
    
    def test_multiplication(self):
        money = Money(Decimal("100"), "USD")
        result = money * 1.5
        assert result.amount == Decimal("150")
    
    def test_currency_mismatch_raises(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("50"), "EUR")
        with pytest.raises(ValueError):
            m1 + m2
    
    def test_string_representation(self):
        money = Money(Decimal("1234567.89"), "USD")
        assert str(money) == "USD 1,234,567.89"


class TestPercentage:
    """Tests for Percentage value object."""
    
    def test_from_percent(self):
        pct = Percentage.from_percent(15.5)
        assert pct.value == Decimal("0.155")
        assert pct.to_percent() == 15.5
    
    def test_from_decimal(self):
        pct = Percentage.from_decimal(0.25)
        assert pct.to_percent() == 25.0
    
    def test_multiplication_with_money(self):
        pct = Percentage.from_percent(10)
        money = Money(Decimal("1000"), "USD")
        result = pct * money
        assert result.amount == Decimal("100")


class TestCompany:
    """Tests for Company entity."""
    
    def test_creation(self):
        company = Company(
            legal_name="Test Company Inc",
            common_name="TestCo",
            ticker="TEST",
            exchange=Exchange.NASDAQ,
            sector=Sector.INFORMATION_TECHNOLOGY,
            industry=Industry.SOFTWARE,
        )
        assert company.legal_name == "Test Company Inc"
        assert company.ticker == "TEST"
    
    def test_ticker_auto_generation(self):
        company = Company(
            legal_name="Test Company Inc",
            common_name="TestCo",
            exchange=Exchange.NASDAQ,
        )
        assert company.ticker == "TESTCO"


class TestFinancialStatement:
    """Tests for FinancialStatement entity."""
    
    def test_creation(self):
        stmt = FinancialStatement(
            company_id=uuid4(),
            period_end=datetime(2023, 12, 31),
            period_type="annual",
            revenue=Money(Decimal("100000000"), "USD"),
            gross_profit=Money(Decimal("75000000"), "USD"),
            net_income=Money(Decimal("15000000"), "USD"),
        )
        assert stmt.revenue.amount == Decimal("100000000")
    
    def test_compute_ratios(self):
        stmt = FinancialStatement(
            revenue=Money(Decimal("100"), "USD"),
            gross_profit=Money(Decimal("75"), "USD"),
            operating_income=Money(Decimal("20"), "USD"),
            net_income=Money(Decimal("15"), "USD"),
            total_assets=Money(Decimal("200"), "USD"),
            total_equity=Money(Decimal("100"), "USD"),
            total_debt=Money(Decimal("30"), "USD"),
            ebitda=Money(Decimal("25"), "USD"),
        )
        stmt.compute_ratios()
        
        assert stmt.gross_margin == 0.75
        assert stmt.operating_margin == 0.20
        assert stmt.net_margin == 0.15
        assert stmt.roe == 0.15
        assert stmt.roa == 0.075
        assert stmt.debt_to_equity == 0.3


class TestIPO:
    """Tests for IPO entity."""
    
    def test_creation(self):
        ipo = IPO(
            symbol="TEST",
            company_name="Test Company",
            exchange=Exchange.NASDAQ,
            sector=Sector.INFORMATION_TECHNOLOGY,
            status=IPOStatus.FILED,
            expected_price_low=Money(Decimal("18"), "USD"),
            expected_price_high=Money(Decimal("22"), "USD"),
        )
        assert ipo.symbol == "TEST"
        assert ipo.status == IPOStatus.FILED
    
    def test_price_range_mid(self):
        ipo = IPO(
            symbol="TEST",
            company_name="Test",
            expected_price_low=Money(Decimal("18"), "USD"),
            expected_price_high=Money(Decimal("22"), "USD"),
        )
        mid = ipo.price_range_mid
        assert mid.amount == Decimal("20")
    
    def test_is_priced(self):
        ipo_filed = IPO(symbol="TEST", status=IPOStatus.FILED)
        ipo_priced = IPO(symbol="TEST", status=IPOStatus.PRICED)
        ipo_listed = IPO(symbol="TEST", status=IPOStatus.LISTED)
        
        assert not ipo_filed.is_priced
        assert ipo_priced.is_priced
        assert ipo_listed.is_priced
    
    def test_is_listed(self):
        ipo_filed = IPO(symbol="TEST", status=IPOStatus.FILED)
        ipo_priced = IPO(symbol="TEST", status=IPOStatus.PRICED)
        ipo_listed = IPO(symbol="TEST", status=IPOStatus.LISTED)
        
        assert not ipo_filed.is_listed
        assert not ipo_priced.is_listed
        assert ipo_listed.is_listed


class TestAnalysisResult:
    """Tests for AnalysisResult entity."""
    
    def test_creation(self):
        result = AnalysisResult(
            ipo_id=uuid4(),
            agent_name=AgentName.FUNDAMENTAL,
            status=AnalysisStatus.COMPLETED,
            score=85.5,
            confidence=0.9,
            reasoning="Strong fundamentals",
            key_findings=["High growth", "Good margins"],
            strengths=["Recurring revenue", "High margins"],
            weaknesses=["Customer concentration"],
        )
        assert result.score == 85.5
        assert result.confidence == 0.9


class TestOverallAnalysis:
    """Tests for OverallAnalysis entity."""
    
    def test_creation(self):
        analysis = OverallAnalysis(
            ipo_id=uuid4(),
            status=AnalysisStatus.COMPLETED,
            overall_score=78.5,
            confidence=0.85,
            financial_strength_score=85.0,
            growth_potential_score=75.0,
            market_opportunity_score=80.0,
            management_quality_score=82.0,
            risk_level_score=70.0,
            bull_case="Strong growth story",
            bear_case="High valuation",
            investment_strategy=InvestmentStrategy.ACCUMULATE,
            time_horizon=TimeHorizon.MEDIUM_TERM,
            risk_level=RiskLevel.MODERATE,
        )
        assert analysis.overall_score == 78.5
        assert analysis.investment_strategy == InvestmentStrategy.ACCUMULATE
    
    def test_risk_score_property(self):
        analysis = OverallAnalysis(risk_level=RiskLevel.HIGH)
        assert analysis.risk_score == 70
        
        analysis.risk_level = RiskLevel.VERY_LOW
        assert analysis.risk_score == 10
    
    def test_recommendation_text(self):
        analysis = OverallAnalysis(
            investment_strategy=InvestmentStrategy.BUY,
        )
        assert "Buy" in analysis.recommendation_text
        
        analysis.investment_strategy = InvestmentStrategy.AVOID
        assert "Avoid" in analysis.recommendation_text


class TestReport:
    """Tests for Report entity."""
    
    def test_creation(self):
        report = Report(
            ipo_id=uuid4(),
            analysis_id=uuid4(),
            title="Test Report",
            executive_summary="Summary",
            ipo_overview="Overview",
            recommendation="Buy",
        )
        assert report.title == "Test Report"
        assert report.format == "markdown"


class TestPrediction:
    """Tests for Prediction value object."""
    
    def test_creation(self):
        pred = Prediction(
            prediction_type="price_change_1m",
            predicted_value=0.15,
            lower_bound=0.05,
            upper_bound=0.25,
            confidence=0.8,
            time_horizon="1 month",
            methodology="DCF + Comps",
        )
        assert pred.predicted_value == 0.15
        assert pred.confidence == 0.8
    
    def test_to_dict(self):
        pred = Prediction(
            prediction_type="price_change_1m",
            predicted_value=0.15,
            lower_bound=0.05,
            upper_bound=0.25,
            confidence=0.8,
            time_horizon="1 month",
        )
        d = pred.to_dict()
        assert d["prediction_type"] == "price_change_1m"
        assert d["predicted_value"] == 0.15


class TestEnums:
    """Tests for domain enums."""
    
    def test_risk_level_scores(self):
        assert RiskLevel.VERY_LOW.value == "very_low"
        assert RiskLevel.EXTREME.value == "extreme"
    
    def test_investment_strategy_ordering(self):
        # Check that strategies have logical ordering
        strategies = list(InvestmentStrategy)
        assert strategies[0] == InvestmentStrategy.AGGRESSIVE_BUY
        assert strategies[-1] == InvestmentStrategy.AVOID
    
    def test_time_horizon_ordering(self):
        horizons = list(TimeHorizon)
        assert horizons[0] == TimeHorizon.INTRADAY
        assert horizons[-1] == TimeHorizon.VERY_LONG_TERM