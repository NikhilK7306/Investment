"""Domain value objects."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from app.domain.enums.enums import (
    Exchange,
    Sector,
    Industry,
    RiskLevel,
    SentimentLabel,
    DataSource,
    VerificationStatus,
)


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts."""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
    
    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, multiplier: float) -> "Money":
        return Money(self.amount * Decimal(str(multiplier)), self.currency)
    
    def __lt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        return self == other or self < other
    
    def __gt__(self, other: "Money") -> bool:
        return not self <= other
    
    def __ge__(self, other: "Money") -> bool:
        return not self < other
    
    def to_float(self) -> float:
        return float(self.amount)
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"


@dataclass(frozen=True)
class Percentage:
    """Value object for percentage values."""
    value: Decimal  # Stored as decimal (e.g., 0.15 for 15%)
    
    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))
    
    @classmethod
    def from_percent(cls, percent: float) -> "Percentage":
        """Create from percentage (e.g., 15.5 for 15.5%)."""
        return cls(Decimal(str(percent)) / Decimal("100"))
    
    @classmethod
    def from_decimal(cls, decimal: float) -> "Percentage":
        """Create from decimal (e.g., 0.155 for 15.5%)."""
        return cls(Decimal(str(decimal)))
    
    def to_percent(self) -> float:
        """Convert to percentage (e.g., 15.5)."""
        return float(self.value * Decimal("100"))
    
    def to_decimal(self) -> float:
        """Convert to decimal (e.g., 0.155)."""
        return float(self.value)
    
    def __mul__(self, other: Money) -> Money:
        return Money(other.amount * self.value, other.currency)
    
    def __str__(self) -> str:
        return f"{self.to_percent():.2f}%"


@dataclass(frozen=True)
class Ratio:
    """Value object for financial ratios."""
    value: Decimal
    name: str
    description: str = ""
    
    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))
    
    def to_float(self) -> float:
        return float(self.value)
    
    def __str__(self) -> str:
        return f"{self.name}: {self.value:.2f}"


@dataclass(frozen=True)
class DateRange:
    """Value object for date ranges."""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("Start date must be before end date")
    
    @property
    def days(self) -> int:
        return (self.end - self.start).days
    
    def contains(self, date: datetime) -> bool:
        return self.start <= date <= self.end
    
    def overlaps(self, other: "DateRange") -> bool:
        return self.start <= other.end and other.start <= self.end


@dataclass(frozen=True)
class PriceRange:
    """Value object for price ranges."""
    low: Money
    high: Money
    
    def __post_init__(self):
        if self.low > self.high:
            raise ValueError("Low price must be <= high price")
        if self.low.currency != self.high.currency:
            raise ValueError("Prices must have same currency")
    
    @property
    def midpoint(self) -> Money:
        return Money((self.low.amount + self.high.amount) / Decimal("2"), self.low.currency)
    
    @property
    def spread(self) -> Money:
        return self.high - self.low
    
    @property
    def spread_percent(self) -> Percentage:
        if self.low.amount == 0:
            return Percentage(Decimal("0"))
        return Percentage.from_decimal(float(self.spread.amount / self.low.amount))


@dataclass(frozen=True)
class Valuation:
    """Company valuation."""
    enterprise_value: Money
    equity_value: Money
    price_per_share: Money
    shares_outstanding: int
    fully_diluted_shares: Optional[int] = None
    methodology: str = ""
    as_of_date: Optional[datetime] = None
    
    @property
    def market_cap(self) -> Money:
        return self.price_per_share * self.shares_outstanding


@dataclass
class FinancialMetrics:
    """Key financial metrics for a company."""
    revenue: Money
    revenue_growth_yoy: Percentage
    revenue_growth_qoq: Percentage
    gross_profit: Money
    gross_margin: Percentage
    operating_income: Money
    operating_margin: Percentage
    net_income: Money
    net_margin: Percentage
    ebitda: Money
    ebitda_margin: Percentage
    free_cash_flow: Money
    fcf_margin: Percentage
    total_assets: Money
    total_liabilities: Money
    total_equity: Money
    total_debt: Money
    cash_and_equivalents: Money
    debt_to_equity: Ratio
    current_ratio: Ratio
    quick_ratio: Ratio
    roe: Percentage
    roa: Percentage
    roic: Percentage
    operating_cash_flow: Optional[Money] = None
    pe_ratio: Optional[Ratio] = None
    pb_ratio: Optional[Ratio] = None
    ps_ratio: Optional[Ratio] = None
    ev_ebitda: Optional[Ratio] = None
    ev_revenue: Optional[Ratio] = None
    peg_ratio: Optional[Ratio] = None
    dividend_yield: Optional[Percentage] = None
    payout_ratio: Optional[Percentage] = None
    
    # Growth metrics
    revenue_cagr_3y: Optional[Percentage] = None
    revenue_cagr_5y: Optional[Percentage] = None
    earnings_cagr_3y: Optional[Percentage] = None
    earnings_cagr_5y: Optional[Percentage] = None
    fcf_cagr_3y: Optional[Percentage] = None
    
    # Quality metrics
    gross_margin_trend: Optional[List[float]] = None
    operating_margin_trend: Optional[List[float]] = None
    fcf_conversion: Optional[Percentage] = None
    earnings_quality: Optional[str] = None
    
    # Per share metrics
    eps_basic: Optional[Money] = None
    eps_diluted: Optional[Money] = None
    book_value_per_share: Optional[Money] = None
    fcf_per_share: Optional[Money] = None
    
    as_of_date: Optional[datetime] = None
    period: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if value is None:
                result[key] = None
            elif isinstance(value, (Money, Percentage, Ratio)):
                result[key] = {
                    "value": float(value.value) if hasattr(value, 'value') else float(value.amount),
                    "display": str(value),
                }
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list):
                result[key] = value
            else:
                result[key] = value
        return result


@dataclass(frozen=True)
class CompanyProfile:
    """Company profile information."""
    legal_name: str
    common_name: str
    description: str
    business_model: str
    sector: Sector
    industry: Industry
    id: Optional[UUID] = None
    ticker: str = ""
    exchange: Exchange = Exchange.OTHER
    sub_industry: Optional[str] = None
    headquarters: str = ""
    country: str = ""
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    website: str = ""
    ceo: str = ""
    cfo: str = ""
    chairman: str = ""
    board_members: List[str] = field(default_factory=list)
    major_shareholders: Dict[str, float] = field(default_factory=dict)  # name -> %
    competitors: List[str] = field(default_factory=list)
    competitive_advantages: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    key_products: List[str] = field(default_factory=list)
    target_markets: List[str] = field(default_factory=list)
    regulatory_environment: str = ""
    esg_score: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "legal_name": self.legal_name,
            "common_name": self.common_name,
            "description": self.description,
            "business_model": self.business_model,
            "sector": self.sector.value,
            "industry": self.industry.value,
            "sub_industry": self.sub_industry,
            "ticker": self.ticker,
            "exchange": self.exchange.value,
            "headquarters": self.headquarters,
            "country": self.country,
            "founded_year": self.founded_year,
            "employee_count": self.employee_count,
            "website": self.website,
            "ceo": self.ceo,
            "cfo": self.cfo,
            "chairman": self.chairman,
            "board_members": self.board_members,
            "major_shareholders": self.major_shareholders,
            "competitors": self.competitors,
            "competitive_advantages": self.competitive_advantages,
            "risk_factors": self.risk_factors,
            "key_products": self.key_products,
            "target_markets": self.target_markets,
            "regulatory_environment": self.regulatory_environment,
            "esg_score": self.esg_score,
        }


@dataclass(frozen=True)
class IPODetails:
    """IPO-specific details."""
    symbol: str
    company_name: str
    exchange: Exchange
    sector: Sector = Sector.UNCLASSIFIED
    industry: Industry = Industry.OTHER
    expected_date: Optional[datetime] = None
    announced_date: Optional[datetime] = None
    filing_date: Optional[datetime] = None
    pricing_date: Optional[datetime] = None
    listed_date: Optional[datetime] = None
    withdrawn_date: Optional[datetime] = None
    status: str = "announced"
    shares_offered: Optional[int] = None
    price_range: Optional[PriceRange] = None
    offer_price: Optional[Money] = None
    valuation: Optional[Valuation] = None
    use_of_proceeds: str = ""
    underwriters: List[str] = field(default_factory=list)
    lead_underwriter: str = ""
    lockup_period_days: Optional[int] = None
    lockup_expiry: Optional[datetime] = None
    greenshoe_option: bool = False
    greenshoe_shares: Optional[int] = None
    minimum_investment: Optional[Money] = None
    retail_allocation_pct: Optional[Percentage] = None
    institutional_allocation_pct: Optional[Percentage] = None
    employee_allocation_pct: Optional[Percentage] = None
    expected_raise: Optional[Money] = None
    registration_statement: str = ""
    prospectus_url: str = ""
    sec_cik: str = ""
    company_id: Optional[UUID] = None
    
    def to_dict(self) -> dict:
        result = {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "exchange": self.exchange.value,
            "sector": self.sector.value,
            "industry": self.industry.value,
            "status": self.status,
            "shares_offered": self.shares_offered,
            "use_of_proceeds": self.use_of_proceeds,
            "underwriters": self.underwriters,
            "lead_underwriter": self.lead_underwriter,
            "lockup_period_days": self.lockup_period_days,
            "greenshoe_option": self.greenshoe_option,
            "greenshoe_shares": self.greenshoe_shares,
            "registration_statement": self.registration_statement,
            "prospectus_url": self.prospectus_url,
            "sec_cik": self.sec_cik,
        }
        
        if self.expected_date:
            result["expected_date"] = self.expected_date.isoformat()
        if self.announced_date:
            result["announced_date"] = self.announced_date.isoformat()
        if self.filing_date:
            result["filing_date"] = self.filing_date.isoformat()
        if self.pricing_date:
            result["pricing_date"] = self.pricing_date.isoformat()
        if self.listed_date:
            result["listed_date"] = self.listed_date.isoformat()
        if self.withdrawn_date:
            result["withdrawn_date"] = self.withdrawn_date.isoformat()
        if self.company_id:
            result["company_id"] = str(self.company_id)
        if self.lockup_expiry:
            result["lockup_expiry"] = self.lockup_expiry.isoformat()
        if self.price_range:
            result["price_range"] = {
                "low": str(self.price_range.low),
                "high": str(self.price_range.high),
                "midpoint": str(self.price_range.midpoint),
            }
        if self.offer_price:
            result["offer_price"] = str(self.offer_price)
        if self.valuation:
            result["valuation"] = {
                "enterprise_value": str(self.valuation.enterprise_value),
                "equity_value": str(self.valuation.equity_value),
                "price_per_share": str(self.valuation.price_per_share),
            }
        if self.minimum_investment:
            result["minimum_investment"] = str(self.minimum_investment)
        if self.retail_allocation_pct:
            result["retail_allocation_pct"] = self.retail_allocation_pct.to_percent()
        if self.institutional_allocation_pct:
            result["institutional_allocation_pct"] = self.institutional_allocation_pct.to_percent()
        if self.employee_allocation_pct:
            result["employee_allocation_pct"] = self.employee_allocation_pct.to_percent()
        if self.expected_raise:
            result["expected_raise"] = str(self.expected_raise)
        
        return result


@dataclass(frozen=True)
class DataPoint:
    """Generic data point with metadata."""
    value: Any
    source: DataSource
    timestamp: datetime
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "source": self.source.value,
            "timestamp": self.timestamp.isoformat(),
            "verification_status": self.verification_status.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SentimentData:
    """Sentiment analysis result."""
    label: SentimentLabel
    score: float  # -1 to 1
    confidence: float
    source: DataSource
    timestamp: datetime
    key_phrases: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "label": self.label.value,
            "score": self.score,
            "confidence": self.confidence,
            "source": self.source.value,
            "timestamp": self.timestamp.isoformat(),
            "key_phrases": self.key_phrases,
            "entities": self.entities,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class RiskFactor:
    """Individual risk factor."""
    category: str
    factor: str
    severity: RiskLevel
    probability: Percentage
    impact: Percentage
    description: str
    evidence: List[str] = field(default_factory=list)
    mitigation: str = ""
    
    @property
    def risk_score(self) -> float:
        """Calculate risk score (0-100)."""
        prob = self.probability.to_decimal()
        imp = self.impact.to_decimal()
        severity_mult = {
            RiskLevel.VERY_LOW: 0.2,
            RiskLevel.LOW: 0.4,
            RiskLevel.MODERATE: 0.6,
            RiskLevel.HIGH: 0.8,
            RiskLevel.VERY_HIGH: 0.9,
            RiskLevel.EXTREME: 1.0,
        }.get(self.severity, 0.5)
        return prob * imp * severity_mult * 100
    
    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "factor": self.factor,
            "severity": self.severity.value,
            "probability": self.probability.to_percent(),
            "impact": self.impact.to_percent(),
            "description": self.description,
            "evidence": self.evidence,
            "mitigation": self.mitigation,
            "risk_score": self.risk_score,
        }


@dataclass(frozen=True)
class ScoreComponent:
    """Individual score component."""
    name: str
    weight: float
    score: float  # 0-100
    reasoning: str
    evidence: List[str] = field(default_factory=list)
    sub_components: List["ScoreComponent"] = field(default_factory=list)
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "weight": self.weight,
            "score": self.score,
            "weighted_score": self.weighted_score,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "sub_components": [sc.to_dict() for sc in self.sub_components],
        }


@dataclass(frozen=True)
class InvestmentThesis:
    """Investment thesis with bull/bear cases."""
    bull_case: str
    bear_case: str
    key_drivers: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    catalysts: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "key_drivers": self.key_drivers,
            "key_risks": self.key_risks,
            "catalysts": self.catalysts,
            "assumptions": self.assumptions,
        }


@dataclass(frozen=True)
class Prediction:
    """Prediction with confidence interval."""
    prediction_type: str
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float  # 0-1
    time_horizon: str
    methodology: str
    assumptions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "prediction_type": self.prediction_type,
            "predicted_value": self.predicted_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence": self.confidence,
            "time_horizon": self.time_horizon,
            "methodology": self.methodology,
            "assumptions": self.assumptions,
            "created_at": self.created_at.isoformat(),
        }