"""Domain enums for IPO Intelligence Agent."""

from enum import Enum, auto
from typing import List


class IPOStatus(str, Enum):
    """IPO lifecycle status."""
    ANNOUNCED = "announced"
    FILED = "filed"
    PRICED = "priced"
    LISTED = "listed"
    WITHDRAWN = "withdrawn"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    # Special states for missing data
    NOT_ANNOUNCED = "not_announced"
    NOT_AVAILABLE = "not_available"
    NOT_APPLICABLE = "not_applicable"


class Exchange(str, Enum):
    """Supported stock exchanges."""
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    LSE = "LSE"
    HKEX = "HKEX"
    TSE = "TSE"
    SSE = "SSE"
    SZSE = "SZSE"
    BSE = "BSE"
    NSE = "NSE"
    TSX = "TSX"
    ASX = "ASX"
    FWB = "FWB"
    EPA = "EPA"
    BIT = "BIT"
    SIX = "SIX"
    OTHER = "OTHER"


class Sector(str, Enum):
    """GICS sector classification."""
    ENERGY = "energy"
    MATERIALS = "materials"
    INDUSTRIALS = "industrials"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    HEALTH_CARE = "health_care"
    FINANCIALS = "financials"
    INFORMATION_TECHNOLOGY = "information_technology"
    COMMUNICATION_SERVICES = "communication_services"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    UNCLASSIFIED = "unclassified"


class Industry(str, Enum):
    """Industry groups (subset for common IPO industries)."""
    # Technology
    SOFTWARE = "software"
    SEMICONDUCTORS = "semiconductors"
    IT_SERVICES = "it_services"
    HARDWARE = "hardware"
    CYBERSECURITY = "cybersecurity"
    AI_ML = "ai_ml"
    FINTECH = "fintech"
    ECOMMERCE = "ecommerce"
    
    # Healthcare
    BIOTECH = "biotech"
    PHARMACEUTICALS = "pharmaceuticals"
    MEDICAL_DEVICES = "medical_devices"
    HEALTHCARE_SERVICES = "healthcare_services"
    DIAGNOSTICS = "diagnostics"
    
    # Financial
    BANKING = "banking"
    INSURANCE = "insurance"
    ASSET_MANAGEMENT = "asset_management"
    PAYMENTS = "payments"
    
    # Consumer
    RETAIL = "retail"
    FOOD_BEVERAGE = "food_beverage"
    APPAREL = "apparel"
    AUTOMOTIVE = "automotive"
    ENTERTAINMENT = "entertainment"
    
    # Industrial
    AEROSPACE = "aerospace"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"
    CONSTRUCTION = "construction"
    
    # Energy
    OIL_GAS = "oil_gas"
    RENEWABLE_ENERGY = "renewable_energy"
    UTILITIES = "utilities"
    
    # Materials
    CHEMICALS = "chemicals"
    METALS_MINING = "metals_mining"
    
    # Real Estate
    REIT = "reit"
    PROPERTY_DEVELOPMENT = "property_development"
    
    OTHER = "other"


class AnalysisDepth(str, Enum):
    """Analysis depth levels."""
    STANDARD = "standard"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"


class AnalysisStatus(str, Enum):
    """Analysis job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class AgentName(str, Enum):
    """Agent identifiers."""
    DISCOVERY = "discovery"
    COLLECTION = "collection"
    FUNDAMENTAL = "fundamental"
    MARKET = "market"
    RISK = "risk"
    SENTIMENT = "sentiment"
    DECISION = "decision"
    REPORT = "report"
    MEMORY = "memory"
    REFLECTION = "reflection"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 20-40%
    MODERATE = "moderate"      # 40-60%
    HIGH = "high"              # 60-80%
    VERY_HIGH = "very_high"    # 80-100%


class SentimentLabel(str, Enum):
    """Sentiment analysis labels."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class DataSource(str, Enum):
    """Data source types."""
    SEC_EDGAR = "sec_edgar"
    EXCHANGE = "exchange"
    FINANCIAL_API = "financial_api"
    NEWS_API = "news_api"
    SOCIAL_MEDIA = "social_media"
    COMPANY_FILING = "company_filing"
    ANALYST_REPORT = "analyst_report"
    ALTERNATIVE_DATA = "alternative_data"
    MANUAL = "manual"


class MemoryType(str, Enum):
    """Memory system types."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    VECTOR = "vector"
    FAILURE = "failure"
    SUCCESS = "success"
    KNOWLEDGE = "knowledge"
    EXPERIENCE = "experience"
    BEST_PRACTICE = "best_practice"
    REFLECTION = "reflection"


class PredictionType(str, Enum):
    """Types of predictions made."""
    PRICE_CHANGE_1D = "price_change_1d"
    PRICE_CHANGE_1W = "price_change_1w"
    PRICE_CHANGE_1M = "price_change_1m"
    PRICE_CHANGE_3M = "price_change_3m"
    PRICE_CHANGE_6M = "price_change_6m"
    PRICE_CHANGE_12M = "price_change_12m"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    OUTPERFORM_MARKET = "outperform_market"
    UNDERPERFORM_MARKET = "underperform_market"
    BANKRUPTCY_RISK = "bankruptcy_risk"
    ACQUISITION_TARGET = "acquisition_target"


class OutcomeStatus(str, Enum):
    """Prediction outcome verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    INCONCLUSIVE = "inconclusive"


class LessonType(str, Enum):
    """Types of lessons learned."""
    PROMPT_IMPROVEMENT = "prompt_improvement"
    TOOL_USAGE = "tool_usage"
    DATA_SOURCE = "data_source"
    REASONING_PATTERN = "reasoning_pattern"
    RISK_FACTOR = "risk_factor"
    SCORING_ADJUSTMENT = "scoring_adjustment"
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    THRESHOLD_CHANGE = "threshold_change"
    ANTI_PATTERN = "anti_pattern"
    BEST_PRACTICE = "best_practice"


class Severity(str, Enum):
    """Error/failure severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailureCategory(str, Enum):
    """Failure categories."""
    HALLUCINATION = "hallucination"
    WRONG_CALCULATION = "wrong_calculation"
    BAD_FINANCIAL_ASSUMPTION = "bad_financial_assumption"
    MISSING_API = "missing_api"
    RATE_LIMIT = "rate_limit"
    WRONG_PROMPT = "wrong_prompt"
    PARSING_FAILURE = "parsing_failure"
    DUPLICATE_DATA = "duplicate_data"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    INVALID_RESPONSE = "invalid_response"
    NETWORK_ERROR = "network_error"
    DATA_QUALITY = "data_quality"
    MODEL_ERROR = "model_error"
    UNKNOWN = "unknown"


class JobType(str, Enum):
    """Background job types."""
    IPO_DISCOVERY = "ipo_discovery"
    DATA_COLLECTION = "data_collection"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    MARKET_ANALYSIS = "market_analysis"
    RISK_ANALYSIS = "risk_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    DECISION_SYNTHESIS = "decision_synthesis"
    REPORT_GENERATION = "report_generation"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    REFLECTION_RUN = "reflection_run"
    OUTCOME_VERIFICATION = "outcome_verification"
    CLEANUP = "cleanup"


class JobStatus(str, Enum):
    """Background job status."""
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"


class ReportFormat(str, Enum):
    """Report output formats."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    EXCEL = "excel"


class TimeHorizon(str, Enum):
    """Investment time horizons."""
    INTRADAY = "intraday"
    SHORT_TERM = "short_term"      # 1-4 weeks
    MEDIUM_TERM = "medium_term"    # 1-3 months
    LONG_TERM = "long_term"        # 3-12 months
    VERY_LONG_TERM = "very_long_term"  # 1+ years


class InvestmentStrategy(str, Enum):
    """Investment strategy recommendations."""
    AGGRESSIVE_BUY = "aggressive_buy"
    BUY = "buy"
    ACCUMULATE = "accumulate"
    HOLD = "hold"
    REDUCE = "reduce"
    SELL = "sell"
    AVOID = "avoid"
    WATCH = "watch"


class VerificationStatus(str, Enum):
    """Data verification status."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    OUTDATED = "outdated"


class DataAvailability(str, Enum):
    """Field-level data availability status."""
    AVAILABLE = "available"
    NOT_ANNOUNCED = "not_announced"
    NOT_AVAILABLE = "not_available"
    NOT_APPLICABLE = "not_applicable"
    PARTIAL = "partial"
    ESTIMATED = "estimated"


# Helper functions
def get_sector_industries(sector: Sector) -> List[Industry]:
    """Get industries belonging to a sector."""
    mapping = {
        Sector.ENERGY: [Industry.OIL_GAS, Industry.RENEWABLE_ENERGY, Industry.UTILITIES],
        Sector.MATERIALS: [Industry.CHEMICALS, Industry.METALS_MINING],
        Sector.INDUSTRIALS: [Industry.AEROSPACE, Industry.MANUFACTURING, Industry.LOGISTICS, Industry.CONSTRUCTION],
        Sector.CONSUMER_DISCRETIONARY: [Industry.RETAIL, Industry.FOOD_BEVERAGE, Industry.APPAREL, Industry.AUTOMOTIVE, Industry.ENTERTAINMENT],
        Sector.CONSUMER_STAPLES: [Industry.FOOD_BEVERAGE, Industry.RETAIL],
        Sector.HEALTH_CARE: [Industry.BIOTECH, Industry.PHARMACEUTICALS, Industry.MEDICAL_DEVICES, Industry.HEALTHCARE_SERVICES, Industry.DIAGNOSTICS],
        Sector.FINANCIALS: [Industry.BANKING, Industry.INSURANCE, Industry.ASSET_MANAGEMENT, Industry.PAYMENTS],
        Sector.INFORMATION_TECHNOLOGY: [Industry.SOFTWARE, Industry.SEMICONDUCTORS, Industry.IT_SERVICES, Industry.HARDWARE, Industry.CYBERSECURITY, Industry.AI_ML, Industry.FINTECH],
        Sector.COMMUNICATION_SERVICES: [Industry.ENTERTAINMENT, Industry.IT_SERVICES],
        Sector.UTILITIES: [Industry.UTILITIES, Industry.RENEWABLE_ENERGY],
        Sector.REAL_ESTATE: [Industry.REIT, Industry.PROPERTY_DEVELOPMENT],
    }
    return mapping.get(sector, [Industry.OTHER])


def get_risk_score(risk_level: RiskLevel) -> float:
    """Convert risk level to numeric score (0-100, lower is better)."""
    mapping = {
        RiskLevel.VERY_LOW: 10,
        RiskLevel.LOW: 25,
        RiskLevel.MODERATE: 50,
        RiskLevel.HIGH: 70,
        RiskLevel.VERY_HIGH: 85,
        RiskLevel.EXTREME: 95,
    }
    return mapping.get(risk_level, 50)


def get_confidence_score(confidence: ConfidenceLevel) -> float:
    """Convert confidence level to numeric score (0-1)."""
    mapping = {
        ConfidenceLevel.VERY_LOW: 0.1,
        ConfidenceLevel.LOW: 0.3,
        ConfidenceLevel.MODERATE: 0.5,
        ConfidenceLevel.HIGH: 0.7,
        ConfidenceLevel.VERY_HIGH: 0.9,
    }
    return mapping.get(confidence, 0.5)


def get_sentiment_score(sentiment: SentimentLabel) -> float:
    """Convert sentiment label to numeric score (-1 to 1)."""
    mapping = {
        SentimentLabel.VERY_NEGATIVE: -0.9,
        SentimentLabel.NEGATIVE: -0.5,
        SentimentLabel.NEUTRAL: 0.0,
        SentimentLabel.POSITIVE: 0.5,
        SentimentLabel.VERY_POSITIVE: 0.9,
    }
    return mapping.get(sentiment, 0.0)


def get_strategy_score(strategy: InvestmentStrategy) -> float:
    """Convert investment strategy to numeric score (-1 to 1)."""
    mapping = {
        InvestmentStrategy.AGGRESSIVE_BUY: 1.0,
        InvestmentStrategy.BUY: 0.7,
        InvestmentStrategy.ACCUMULATE: 0.4,
        InvestmentStrategy.HOLD: 0.0,
        InvestmentStrategy.WATCH: 0.0,
        InvestmentStrategy.REDUCE: -0.4,
        InvestmentStrategy.SELL: -0.7,
        InvestmentStrategy.AVOID: -1.0,
    }
    return mapping.get(strategy, 0.0)