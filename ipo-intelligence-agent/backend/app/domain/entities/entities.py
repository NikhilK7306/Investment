"""Domain entities for IPO Intelligence Agent."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from app.domain.enums.enums import (
    IPOStatus,
    Exchange,
    Sector,
    Industry,
    RiskLevel,
    SentimentLabel,
    AnalysisStatus,
    AgentName,
    AgentStatus,
    PredictionType,
    OutcomeStatus,
    InvestmentStrategy,
    TimeHorizon,
)
from app.domain.value_objects.value_objects import Money, Prediction


@dataclass
class Company:
    """Company entity."""
    id: UUID = field(default_factory=uuid4)
    legal_name: str = ""
    common_name: str = ""
    ticker: str = ""
    exchange: Exchange = Exchange.OTHER
    sector: Sector = Sector.UNCLASSIFIED
    industry: Industry = Industry.OTHER
    description: str = ""
    business_model: str = ""
    competitive_advantage: str = ""
    headquarters: str = ""
    founded_date: Optional[datetime] = None
    employee_count: Optional[int] = None
    website: str = ""
    ceo: str = ""
    cfo: str = ""
    coo: str = ""
    board_members: List[str] = field(default_factory=list)
    major_shareholders: Dict[str, float] = field(default_factory=dict)  # name -> percentage
    ipo_date: Optional[datetime] = None
    ipo_price: Optional[Money] = None
    ipo_shares: Optional[int] = None
    market_cap: Optional[Money] = None
    enterprise_value: Optional[Money] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.ticker and self.common_name:
            self.ticker = self.common_name.upper().replace(" ", "")[:5]


@dataclass
class FinancialStatement:
    """Financial statement period data."""
    id: UUID = field(default_factory=uuid4)
    company_id: UUID = field(default_factory=uuid4)
    period_end: datetime = field(default_factory=datetime.utcnow)
    period_type: str = "quarterly"  # quarterly, annual, ttm
    
    # Income Statement
    revenue: Optional[Money] = None
    cost_of_revenue: Optional[Money] = None
    gross_profit: Optional[Money] = None
    operating_expenses: Optional[Money] = None
    operating_income: Optional[Money] = None
    ebitda: Optional[Money] = None
    net_income: Optional[Money] = None
    eps_basic: Optional[Decimal] = None
    eps_diluted: Optional[Money] = None
    shares_outstanding: Optional[int] = None
    shares_diluted: Optional[int] = None
    
    # Balance Sheet
    total_assets: Optional[Money] = None
    total_liabilities: Optional[Money] = None
    total_equity: Optional[Money] = None
    cash_and_equivalents: Optional[Money] = None
    short_term_investments: Optional[Money] = None
    total_debt: Optional[Money] = None
    long_term_debt: Optional[Money] = None
    short_term_debt: Optional[Money] = None
    working_capital: Optional[Money] = None
    
    # Cash Flow
    operating_cash_flow: Optional[Money] = None
    investing_cash_flow: Optional[Money] = None
    financing_cash_flow: Optional[Money] = None
    free_cash_flow: Optional[Money] = None
    capex: Optional[Money] = None
    
    # Ratios (computed)
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    debt_to_equity: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Growth (YoY, QoQ)
    revenue_growth_yoy: Optional[float] = None
    revenue_growth_qoq: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    earnings_growth_qoq: Optional[float] = None
    fcf_growth_yoy: Optional[float] = None
    
    source: str = ""
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def compute_ratios(self):
        """Compute financial ratios from raw data."""
        if self.revenue and self.revenue.amount > 0:
            if self.gross_profit:
                self.gross_margin = float(self.gross_profit.amount / self.revenue.amount)
            if self.operating_income:
                self.operating_margin = float(self.operating_income.amount / self.revenue.amount)
            if self.net_income:
                self.net_margin = float(self.net_income.amount / self.revenue.amount)
        
        if self.total_assets and self.total_assets.amount > 0:
            if self.net_income:
                self.roa = float(self.net_income.amount / self.total_assets.amount)
        
        if self.total_equity and self.total_equity.amount > 0:
            if self.net_income:
                self.roe = float(self.net_income.amount / self.total_equity.amount)
        
        if self.total_debt and self.total_equity and self.total_equity.amount > 0:
            self.debt_to_equity = float(self.total_debt.amount / self.total_equity.amount)
        
        if self.ebitda and self.ebitda.amount > 0:
            if self.total_debt:
                self.debt_to_ebitda = float(self.total_debt.amount / self.ebitda.amount)
            if self.operating_income:
                self.interest_coverage = float(self.operating_income.amount / self.ebitda.amount)
        
        if self.total_liabilities and self.total_liabilities.amount > 0:
            if self.cash_and_equivalents:
                current_assets = self.cash_and_equivalents.amount
                if self.short_term_investments:
                    current_assets += self.short_term_investments.amount
                self.current_ratio = float(current_assets / self.total_liabilities.amount)


@dataclass
class IPO:
    """IPO entity."""
    id: UUID = field(default_factory=uuid4)
    symbol: str = ""
    company_id: UUID = field(default_factory=uuid4)
    company_name: str = ""
    exchange: Exchange = Exchange.OTHER
    sector: Sector = Sector.UNCLASSIFIED
    industry: Industry = Industry.OTHER
    status: IPOStatus = IPOStatus.ANNOUNCED
    
    # Timeline
    announced_date: Optional[datetime] = None
    filed_date: Optional[datetime] = None
    priced_date: Optional[datetime] = None
    listed_date: Optional[datetime] = None
    withdrawn_date: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    
    # Offer Details
    expected_price_low: Optional[Money] = None
    expected_price_high: Optional[Money] = None
    priced_price: Optional[Money] = None
    shares_offered: Optional[int] = None
    shares_sold: Optional[int] = None
    overallotment_option: bool = False
    overallotment_shares: Optional[int] = None
    
    # Valuation
    expected_valuation_low: Optional[Money] = None
    expected_valuation_high: Optional[Money] = None
    priced_valuation: Optional[Money] = None
    post_money_valuation: Optional[Money] = None
    
    # Underwriters
    lead_underwriters: List[str] = field(default_factory=list)
    co_managers: List[str] = field(default_factory=list)
    
    # Lockup
    lockup_expiry: Optional[datetime] = None
    lockup_days: Optional[int] = None
    
    # Documents
    prospectus_url: str = ""
    filing_urls: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def price_range_mid(self) -> Optional[Money]:
        if self.expected_price_low and self.expected_price_high:
            mid = (self.expected_price_low.amount + self.expected_price_high.amount) / 2
            return Money(mid, self.expected_price_low.currency)
        return None
    
    @property
    def is_priced(self) -> bool:
        return self.status in (IPOStatus.PRICED, IPOStatus.LISTED)
    
    @property
    def is_listed(self) -> bool:
        return self.status == IPOStatus.LISTED


@dataclass
class AnalysisResult:
    """Analysis result from an agent."""
    id: UUID = field(default_factory=uuid4)
    ipo_id: UUID = field(default_factory=uuid4)
    agent_name: AgentName = AgentName.FUNDAMENTAL
    status: AnalysisStatus = AnalysisStatus.PENDING
    
    # Scores
    score: float = 0.0  # 0-100
    confidence: float = 0.0  # 0-1
    
    # Reasoning
    reasoning: str = ""
    key_findings: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    # Detailed breakdown
    sub_scores: Dict[str, float] = field(default_factory=dict)
    factor_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    
    # Predictions
    predictions: List[Prediction] = field(default_factory=list)
    
    # Metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    retry_count: int = 0
    model_version: str = ""
    prompt_version: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OverallAnalysis:
    """Aggregated analysis from all agents."""
    id: UUID = field(default_factory=uuid4)
    ipo_id: UUID = field(default_factory=uuid4)
    status: AnalysisStatus = AnalysisStatus.PENDING
    
    # Overall scores
    overall_score: float = 0.0
    confidence: float = 0.0
    
    # Weighted component scores
    financial_strength_score: float = 0.0
    growth_potential_score: float = 0.0
    market_opportunity_score: float = 0.0
    management_quality_score: float = 0.0
    risk_level_score: float = 0.0  # Inverted (lower risk = higher score)
    
    # Score breakdown
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    bull_case: str = ""
    bear_case: str = ""
    key_risks: List[str] = field(default_factory=list)
    key_catalysts: List[str] = field(default_factory=list)
    investment_strategy: InvestmentStrategy = InvestmentStrategy.WATCH
    time_horizon: TimeHorizon = TimeHorizon.MEDIUM_TERM
    
    # Risk assessment
    risk_level: RiskLevel = RiskLevel.MODERATE
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Sentiment
    sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    sentiment_score: float = 0.0
    sentiment_drivers: List[str] = field(default_factory=list)
    
    # Agent results
    agent_results: List[AnalysisResult] = field(default_factory=list)
    
    # Metadata
    completed_at: Optional[datetime] = None
    model_version: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def risk_score(self) -> float:
        """Get risk score (0-100, lower is better)."""
        mapping = {
            RiskLevel.VERY_LOW: 10,
            RiskLevel.LOW: 25,
            RiskLevel.MODERATE: 50,
            RiskLevel.HIGH: 70,
            RiskLevel.VERY_HIGH: 85,
            RiskLevel.EXTREME: 95,
        }
        return mapping.get(self.risk_level, 50)
    
    @property
    def recommendation_text(self) -> str:
        """Get human-readable recommendation."""
        mapping = {
            InvestmentStrategy.AGGRESSIVE_BUY: "Strong Buy - Exceptional opportunity with favorable risk/reward",
            InvestmentStrategy.BUY: "Buy - Attractive opportunity with manageable risks",
            InvestmentStrategy.ACCUMULATE: "Accumulate - Good opportunity, consider building position",
            InvestmentStrategy.HOLD: "Hold - Fair value, maintain existing position",
            InvestmentStrategy.WATCH: "Watch - Monitor for better entry point or catalyst",
            InvestmentStrategy.REDUCE: "Reduce - Consider trimming position on strength",
            InvestmentStrategy.SELL: "Sell - Unfavorable risk/reward, consider exiting",
            InvestmentStrategy.AVOID: "Avoid - High risk of significant loss",
        }
        return mapping.get(self.investment_strategy, "No recommendation")


@dataclass
class InvestmentThesis:
    """Investment thesis entity."""
    id: UUID = field(default_factory=uuid4)
    analysis_id: UUID = field(default_factory=uuid4)
    bull_case: str = ""
    bear_case: str = ""
    key_drivers: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    catalysts: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskFactor:
    """Risk factor entity."""
    id: UUID = field(default_factory=uuid4)
    analysis_id: UUID = field(default_factory=uuid4)
    category: str = ""
    factor: str = ""
    severity: str = ""
    probability: float = 0.0
    impact: float = 0.0
    description: str = ""
    evidence: List[str] = field(default_factory=list)
    mitigation: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreComponent:
    """Score component breakdown."""
    id: UUID = field(default_factory=uuid4)
    analysis_id: UUID = field(default_factory=uuid4)
    name: str = ""
    weight: float = 0.0
    score: float = 0.0
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    sub_components: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Prediction:
    """Prediction entity."""
    id: UUID = field(default_factory=uuid4)
    analysis_id: UUID = field(default_factory=uuid4)
    prediction_type: str = ""
    predicted_value: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    confidence: float = 0.5
    time_horizon: str = ""
    methodology: str = ""
    assumptions: List[str] = field(default_factory=list)
    actual_value: Optional[float] = None
    accuracy: Optional[float] = None
    outcome_status: str = "pending"
    verified_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Investment research report."""
    id: UUID = field(default_factory=uuid4)
    ipo_id: UUID = field(default_factory=uuid4)
    analysis_id: UUID = field(default_factory=uuid4)
    
    # Content
    title: str = ""
    executive_summary: str = ""
    
    # Sections
    ipo_overview: str = ""
    company_background: str = ""
    industry_analysis: str = ""
    financial_analysis: str = ""
    valuation_analysis: str = ""
    risk_analysis: str = ""
    management_assessment: str = ""
    sentiment_analysis: str = ""
    bull_case: str = ""
    bear_case: str = ""
    investment_thesis: str = ""
    recommendation: str = ""
    
    # Structured data
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    financial_tables: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    
    # References
    sources: List[Dict[str, str]] = field(default_factory=list)
    disclaimers: List[str] = field(default_factory=list)
    
    # Metadata
    format: str = "markdown"
    version: str = "1.0"
    generated_by: str = ""
    model_version: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEntry:
    """Base memory entry."""
    id: UUID = field(default_factory=uuid4)
    memory_type: str = ""
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    ttl_days: Optional[int] = None
    
    def is_expired(self) -> bool:
        if self.ttl_days is None:
            return False
        from datetime import timedelta
        return datetime.utcnow() - self.created_at > timedelta(days=self.ttl_days)


@dataclass
class ExperienceMemory(MemoryEntry):
    """Experience memory entry - past analyses and outcomes."""
    ipo_symbol: str = ""
    situation_description: str = ""
    prediction_made: str = ""
    actual_outcome: str = ""
    learning: str = ""
    accuracy: float = 0.0
    prediction_id: Optional[UUID] = None
    outcome_id: Optional[UUID] = None
    confidence_at_prediction: float = 0.0
    time_to_outcome_days: Optional[int] = None
    reference_count: int = 0


@dataclass
class FailureMemory(MemoryEntry):
    """Failure memory entry."""
    failure_id: str = ""
    agent_name: AgentName = AgentName.FUNDAMENTAL
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    root_cause: str = ""
    attempted_fix: str = ""
    resolved: bool = False
    resolution: str = ""
    confidence: float = 0.0
    category: str = ""
    severity: str = "medium"
    occurrences: int = 1
    similarity_hash: str = ""
    last_occurrence: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SuccessMemory(MemoryEntry):
    """Success memory entry."""
    success_id: str = ""
    agent_name: AgentName = AgentName.FUNDAMENTAL
    strategy_description: str = ""
    prompt_used: str = ""
    tool_sequence: List[str] = field(default_factory=list)
    api_sequence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    success_rate: float = 0.0
    context_hash: str = ""
    reuse_count: int = 0
    last_reused: Optional[datetime] = None


@dataclass
class KnowledgeMemory(MemoryEntry):
    """Knowledge memory entry."""
    concept: str = ""
    description: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    domain: str = ""
    tags: List[str] = field(default_factory=list)
    version: int = 1
    supersedes: Optional[UUID] = None


@dataclass
class BestPracticeMemory(MemoryEntry):
    """Best practice memory entry."""
    practice_name: str = ""
    description: str = ""
    applicable_context: Dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    version: int = 1


@dataclass
class ReflectionMemory(MemoryEntry):
    """Reflection memory entry."""
    prediction_id: UUID = field(default_factory=uuid4)
    ipo_symbol: str = ""
    prediction_type: PredictionType = PredictionType.PRICE_CHANGE_1M
    predicted_value: float = 0.0
    actual_value: float = 0.0
    accuracy: float = 0.0
    error: float = 0.0
    mistakes_identified: List[str] = field(default_factory=list)
    correct_assumptions: List[str] = field(default_factory=list)
    missing_factors: List[str] = field(default_factory=list)
    lessons_extracted: List[str] = field(default_factory=list)
    prompt_improvements: List[str] = field(default_factory=list)
    strategy_changes: List[str] = field(default_factory=list)
    knowledge_updates: List[str] = field(default_factory=list)
    processed: bool = False


@dataclass
class Lesson:
    """Extracted lesson from reflection."""
    id: UUID = field(default_factory=uuid4)
    lesson_type: str = ""
    title: str = ""
    description: str = ""
    do: List[str] = field(default_factory=list)
    dont: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    known_bugs: List[str] = field(default_factory=list)
    prompt_improvements: List[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    applicable_agents: List[AgentName] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    supersedes: Optional[UUID] = None


@dataclass
class Conversation:
    """Chat conversation entity."""
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[str] = None
    session_id: str = ""
    ipo_symbol: Optional[str] = None
    title: str = ""
    context_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0


@dataclass
class ChatMessage:
    """Chat message entity."""
    id: UUID = field(default_factory=uuid4)
    conversation_id: UUID = field(default_factory=uuid4)
    role: str = ""  # user, assistant, system
    content: str = ""
    agent_name: Optional[str] = None
    ipo_symbol: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


# Alias for backward compatibility
Analysis = OverallAnalysis