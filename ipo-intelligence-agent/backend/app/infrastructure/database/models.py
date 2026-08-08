"""SQLAlchemy database models for IPO Intelligence Agent."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
    Numeric,
    Integer,
    Boolean,
    JSON,
    ARRAY,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY as PG_ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.domain.enums.enums import (
    IPOStatus,
    Exchange,
    Sector,
    Industry,
    RiskLevel,
    SentimentLabel,
    AnalysisStatus,
    AgentName,
    PredictionType,
    OutcomeStatus,
    InvestmentStrategy,
    TimeHorizon,
    MemoryType,
    LessonType,
    Severity,
    FailureCategory,
    JobType,
    JobStatus,
    VerificationStatus,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class CompanyModel(Base):
    """Company profile model."""
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    exchange: Mapped[Exchange] = mapped_column(SQLEnum(Exchange), default=Exchange.OTHER)
    sector: Mapped[Sector] = mapped_column(SQLEnum(Sector), default=Sector.UNCLASSIFIED)
    industry: Mapped[Industry] = mapped_column(SQLEnum(Industry), default=Industry.OTHER)
    description: Mapped[str] = mapped_column(Text, default="")
    business_model: Mapped[str] = mapped_column(Text, default="")
    competitive_advantage: Mapped[str] = mapped_column(Text, default="")
    headquarters: Mapped[str] = mapped_column(String(255), default="")
    founded_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    website: Mapped[str] = mapped_column(String(255), default="")
    ceo: Mapped[str] = mapped_column(String(255), default="")
    cfo: Mapped[str] = mapped_column(String(255), default="")
    coo: Mapped[str] = mapped_column(String(255), default="")
    board_members: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    major_shareholders: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)
    ipo_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ipo_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    ipo_shares: Mapped[Optional[int]] = mapped_column(Integer)
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    enterprise_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    financials: Mapped[List["FinancialStatementModel"]] = relationship(back_populates="company", lazy="dynamic")
    ipos: Mapped[List["IPOModel"]] = relationship(back_populates="company", lazy="dynamic")
    analyses: Mapped[List["AnalysisModel"]] = relationship(back_populates="company", lazy="dynamic")


class FinancialStatementModel(Base):
    """Financial statement model."""
    __tablename__ = "financial_statements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    period_type: Mapped[str] = mapped_column(String(20), default="quarterly")  # quarterly, annual, ttm

    # Income Statement
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    cost_of_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    gross_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    operating_expenses: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    operating_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    eps_basic: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    eps_diluted: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    shares_outstanding: Mapped[Optional[int]] = mapped_column(Integer)
    shares_diluted: Mapped[Optional[int]] = mapped_column(Integer)

    # Balance Sheet
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    cash_and_equivalents: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    short_term_investments: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    long_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    short_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    working_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # Cash Flow
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    investing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    financing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    capex: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # Ratios (computed)
    gross_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    operating_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    net_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    roe: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    roa: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    roic: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    debt_to_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    debt_to_ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    current_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    quick_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    interest_coverage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))

    # Growth
    revenue_growth_yoy: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    revenue_growth_qoq: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    earnings_growth_yoy: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    earnings_growth_qoq: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    fcf_growth_yoy: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))

    source: Mapped[str] = mapped_column(String(100), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    company: Mapped["CompanyModel"] = relationship(back_populates="financials")

    __table_args__ = (
        Index("ix_financials_company_period", "company_id", "period_end"),
        Index("ix_financials_company_period_type", "company_id", "period_type", "period_end"),
    )


class IPOModel(Base):
    """IPO model."""
    __tablename__ = "ipos"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[Exchange] = mapped_column(SQLEnum(Exchange), default=Exchange.OTHER)
    sector: Mapped[Sector] = mapped_column(SQLEnum(Sector), default=Sector.UNCLASSIFIED)
    industry: Mapped[Industry] = mapped_column(SQLEnum(Industry), default=Industry.OTHER)
    status: Mapped[IPOStatus] = mapped_column(SQLEnum(IPOStatus), default=IPOStatus.ANNOUNCED, index=True)

    # Timeline
    announced_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    filed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    priced_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    listed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    withdrawn_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expected_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    # Offer Details
    expected_price_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    expected_price_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    priced_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    shares_offered: Mapped[Optional[int]] = mapped_column(Integer)
    shares_sold: Mapped[Optional[int]] = mapped_column(Integer)
    overallotment_option: Mapped[bool] = mapped_column(Boolean, default=False)
    overallotment_shares: Mapped[Optional[int]] = mapped_column(Integer)

    # Valuation
    expected_valuation_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    expected_valuation_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    priced_valuation: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    post_money_valuation: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # Underwriters
    lead_underwriters: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    co_managers: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Lockup
    lockup_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    lockup_days: Mapped[Optional[int]] = mapped_column(Integer)

    # Documents
    prospectus_url: Mapped[str] = mapped_column(String(500), default="")
    filing_urls: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    company: Mapped["CompanyModel"] = relationship(back_populates="ipos")
    analyses: Mapped[List["AnalysisModel"]] = relationship(back_populates="ipo", lazy="dynamic")
    reports: Mapped[List["ReportModel"]] = relationship(back_populates="ipo", lazy="dynamic")


class AnalysisModel(Base):
    """Analysis result model."""
    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ipo_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("ipos.id"), index=True)
    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    status: Mapped[AnalysisStatus] = mapped_column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING, index=True)

    # Overall scores
    overall_score: Mapped[float] = mapped_column(default=0.0)
    confidence: Mapped[float] = mapped_column(default=0.0)

    # Weighted component scores
    financial_strength_score: Mapped[float] = mapped_column(default=0.0)
    growth_potential_score: Mapped[float] = mapped_column(default=0.0)
    market_opportunity_score: Mapped[float] = mapped_column(default=0.0)
    management_quality_score: Mapped[float] = mapped_column(default=0.0)
    risk_level_score: Mapped[float] = mapped_column(default=0.0)

    # Score breakdown
    score_breakdown: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)

    # Recommendations
    bull_case: Mapped[str] = mapped_column(Text, default="")
    bear_case: Mapped[str] = mapped_column(Text, default="")
    key_risks: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    key_catalysts: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    investment_strategy: Mapped[InvestmentStrategy] = mapped_column(SQLEnum(InvestmentStrategy), default=InvestmentStrategy.WATCH)
    time_horizon: Mapped[TimeHorizon] = mapped_column(SQLEnum(TimeHorizon), default=TimeHorizon.MEDIUM_TERM)

    # Risk assessment
    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel), default=RiskLevel.MODERATE)
    risk_factors: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Sentiment
    sentiment: Mapped[SentimentLabel] = mapped_column(SQLEnum(SentimentLabel), default=SentimentLabel.NEUTRAL)
    sentiment_score: Mapped[float] = mapped_column(default=0.0)
    sentiment_drivers: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Agent results
    agent_results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    model_version: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    ipo: Mapped["IPOModel"] = relationship(back_populates="analyses")
    company: Mapped["CompanyModel"] = relationship(back_populates="analyses")
    score_components: Mapped[List["ScoreComponentModel"]] = relationship(back_populates="analysis", lazy="dynamic")
    risk_factors: Mapped[List["RiskFactorModel"]] = relationship(back_populates="analysis", lazy="dynamic")
    investment_thesis: Mapped[Optional["InvestmentThesisModel"]] = relationship(back_populates="analysis", uselist=False)
    predictions: Mapped[List["PredictionModel"]] = relationship(back_populates="analysis", lazy="dynamic")
    reports: Mapped[List["ReportModel"]] = relationship(back_populates="analysis", lazy="dynamic")


class ScoreComponentModel(Base):
    """Score component breakdown."""
    __tablename__ = "score_components"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(default=0.0)
    score: Mapped[float] = mapped_column(default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    sub_components: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)

    analysis: Mapped["AnalysisModel"] = relationship(back_populates="score_components")


class RiskFactorModel(Base):
    """Risk factor model."""
    __tablename__ = "risk_factors"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    factor: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel), default=RiskLevel.MODERATE)
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.5"))
    impact: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.5"))
    description: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    mitigation: Mapped[str] = mapped_column(Text, default="")

    analysis: Mapped["AnalysisModel"] = relationship(back_populates="risk_factors")


class InvestmentThesisModel(Base):
    """Investment thesis model."""
    __tablename__ = "investment_theses"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), unique=True)
    bull_case: Mapped[str] = mapped_column(Text, default="")
    bear_case: Mapped[str] = mapped_column(Text, default="")
    key_drivers: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    key_risks: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    catalysts: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    assumptions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    analysis: Mapped["AnalysisModel"] = relationship(back_populates="investment_thesis")


class PredictionModel(Base):
    """Prediction model."""
    __tablename__ = "predictions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), index=True)
    prediction_type: Mapped[PredictionType] = mapped_column(SQLEnum(PredictionType), index=True)
    predicted_value: Mapped[float] = mapped_column(default=0.0)
    lower_bound: Mapped[float] = mapped_column(default=0.0)
    upper_bound: Mapped[float] = mapped_column(default=0.0)
    confidence: Mapped[float] = mapped_column(default=0.5)
    time_horizon: Mapped[str] = mapped_column(String(50), default="")
    methodology: Mapped[str] = mapped_column(Text, default="")
    assumptions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Outcome verification
    actual_value: Mapped[Optional[float]] = mapped_column(default=None)
    accuracy: Mapped[Optional[float]] = mapped_column(default=None)
    outcome_status: Mapped[OutcomeStatus] = mapped_column(SQLEnum(OutcomeStatus), default=OutcomeStatus.PENDING)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    analysis: Mapped["AnalysisModel"] = relationship(back_populates="predictions")
    reflection: Mapped[Optional["ReflectionMemoryModel"]] = relationship(back_populates="prediction", uselist=False)


class ReportModel(Base):
    """Report model."""
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ipo_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("ipos.id"), index=True)
    analysis_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), index=True)

    title: Mapped[str] = mapped_column(String(255), default="")
    executive_summary: Mapped[str] = mapped_column(Text, default="")

    # Sections
    ipo_overview: Mapped[str] = mapped_column(Text, default="")
    company_background: Mapped[str] = mapped_column(Text, default="")
    industry_analysis: Mapped[str] = mapped_column(Text, default="")
    financial_analysis: Mapped[str] = mapped_column(Text, default="")
    valuation_analysis: Mapped[str] = mapped_column(Text, default="")
    risk_analysis: Mapped[str] = mapped_column(Text, default="")
    management_assessment: Mapped[str] = mapped_column(Text, default="")
    sentiment_analysis: Mapped[str] = mapped_column(Text, default="")
    bull_case: Mapped[str] = mapped_column(Text, default="")
    bear_case: Mapped[str] = mapped_column(Text, default="")
    investment_thesis: Mapped[str] = mapped_column(Text, default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")

    # Structured data
    key_metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    financial_tables: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    charts: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)

    # References
    sources: Mapped[List[Dict[str, str]]] = mapped_column(JSONB, default=list)
    disclaimers: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    format: Mapped[str] = mapped_column(String(20), default="markdown")
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    generated_by: Mapped[str] = mapped_column(String(100), default="")
    model_version: Mapped[str] = mapped_column(String(50), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    ipo: Mapped["IPOModel"] = relationship(back_populates="reports")
    analysis: Mapped["AnalysisModel"] = relationship(back_populates="reports")


# Memory Models
class MemoryEntryModel(Base):
    """Base memory entry model."""
    __tablename__ = "memory_entries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    memory_type: Mapped[MemoryType] = mapped_column(SQLEnum(MemoryType), index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(3072))
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ttl_days: Mapped[Optional[int]] = mapped_column(Integer)


class ExperienceMemoryModel(Base):
    """Experience memory model."""
    __tablename__ = "experience_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ipo_symbol: Mapped[str] = mapped_column(String(20), index=True)
    situation_description: Mapped[str] = mapped_column(Text, nullable=False)
    prediction_made: Mapped[str] = mapped_column(Text, nullable=False)
    actual_outcome: Mapped[str] = mapped_column(Text, default="")
    learning: Mapped[str] = mapped_column(Text, default="")
    accuracy: Mapped[float] = mapped_column(default=0.0)
    prediction_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("predictions.id"))
    outcome_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    confidence_at_prediction: Mapped[float] = mapped_column(default=0.0)
    time_to_outcome_days: Mapped[Optional[int]] = mapped_column(Integer)
    reference_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    __table_args__ = (
        Index("ix_experience_ipo_symbol", "ipo_symbol"),
    )


class FailureMemoryModel(Base):
    """Failure memory model."""
    __tablename__ = "failure_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    failure_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    agent_name: Mapped[AgentName] = mapped_column(SQLEnum(AgentName), index=True)
    error_type: Mapped[str] = mapped_column(String(100), index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str] = mapped_column(Text, default="")
    root_cause: Mapped[str] = mapped_column(Text, default="")
    attempted_fix: Mapped[str] = mapped_column(Text, default="")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    resolution: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(default=0.0)
    category: Mapped[FailureCategory] = mapped_column(SQLEnum(FailureCategory), default=FailureCategory.UNKNOWN, index=True)
    severity: Mapped[Severity] = mapped_column(SQLEnum(Severity), default=Severity.MEDIUM)
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    similarity_hash: Mapped[str] = mapped_column(String(64), index=True)
    last_occurrence: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    ipo_symbol: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    analysis_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    __table_args__ = (
        Index("ix_failure_agent_category", "agent_name", "category"),
        Index("ix_failure_unresolved", "resolved", "last_occurrence"),
    )


class SuccessMemoryModel(Base):
    """Success memory model."""
    __tablename__ = "success_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    success_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    agent_name: Mapped[AgentName] = mapped_column(SQLEnum(AgentName), index=True)
    strategy_description: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_used: Mapped[str] = mapped_column(Text, default="")
    tool_sequence: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    api_sequence: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    confidence: Mapped[float] = mapped_column(default=0.0)
    success_rate: Mapped[float] = mapped_column(default=0.0)
    context_hash: Mapped[str] = mapped_column(String(64), index=True)
    reuse_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reused: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ipo_symbol: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    analysis_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


class KnowledgeMemoryModel(Base):
    """Knowledge memory model."""
    __tablename__ = "knowledge_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    concept: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float] = mapped_column(default=0.0)
    domain: Mapped[str] = mapped_column(String(100), index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    supersedes: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


class BestPracticeMemoryModel(Base):
    """Best practice memory model."""
    __tablename__ = "best_practice_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    practice_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applicable_context: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    success_rate: Mapped[float] = mapped_column(default=0.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


class ReflectionMemoryModel(Base):
    """Reflection memory model."""
    __tablename__ = "reflection_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    prediction_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("predictions.id"), unique=True, index=True)
    ipo_symbol: Mapped[str] = mapped_column(String(20), index=True)
    prediction_type: Mapped[PredictionType] = mapped_column(SQLEnum(PredictionType))
    predicted_value: Mapped[float] = mapped_column(default=0.0)
    actual_value: Mapped[float] = mapped_column(default=0.0)
    accuracy: Mapped[float] = mapped_column(default=0.0)
    error: Mapped[float] = mapped_column(default=0.0)
    mistakes_identified: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    correct_assumptions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    missing_factors: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    lessons_extracted: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    prompt_improvements: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    strategy_changes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    knowledge_updates: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Relationships
    prediction: Mapped["PredictionModel"] = relationship(back_populates="reflection")


class LessonModel(Base):
    """Lesson learned model."""
    __tablename__ = "lessons"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    lesson_type: Mapped[LessonType] = mapped_column(SQLEnum(LessonType), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    do: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    dont: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    best_practices: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    anti_patterns: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    known_bugs: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    prompt_improvements: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    confidence: Mapped[float] = mapped_column(default=0.0)
    evidence: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    applicable_agents: Mapped[List[AgentName]] = mapped_column(PG_ARRAY(SQLEnum(AgentName)), default=list)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    supersedes: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


# User and Auth Models
class UserModel(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    roles: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    permissions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class APIKeyModel(Base):
    """API key model."""
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    user: Mapped["UserModel"] = relationship()


# Job Models
class JobModel(Base):
    """Background job model."""
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type: Mapped[JobType] = mapped_column(SQLEnum(JobType), index=True)
    status: Mapped[JobStatus] = mapped_column(SQLEnum(JobStatus), default=JobStatus.QUEUED, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    error: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_jobs_status_scheduled", "status", "scheduled_at"),
        Index("ix_jobs_type_status", "job_type", "status"),
    )


# Event Model
class DomainEventModel(Base):
    """Domain event model for event sourcing."""
    __tablename__ = "domain_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    extra_data: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), index=True)

    __table_args__ = (
        Index("ix_events_aggregate_version", "aggregate_id", "version"),
    )