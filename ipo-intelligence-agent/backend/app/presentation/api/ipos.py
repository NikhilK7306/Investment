"""API router for IPOs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.enums.enums import Exchange, Sector, Industry, IPOStatus
from app.application.use_cases.ipo_use_cases import (
    DiscoverIPOsUseCase,
    GetIPODetailsUseCase,
    GetUpcomingIPOsUseCase as ListUpcomingIPOsUseCase,
    SearchIPOsUseCase,
    GetRecentIPOsUseCase as GetRecentlyListedIPOsUseCase,
    CreateIPOUseCase,
    UpdateIPOStatusUseCase,
    GetCompanyProfileUseCase,
    CreateCompanyProfileUseCase,
    ListCompaniesBySectorUseCase,
    ListCompaniesByIndustryUseCase,
)
from app.infrastructure.repositories.sql_repositories import (
    SQLIPORepository,
    SQLCompanyRepository,
)
from app.infrastructure.database.session import get_db_session


router = APIRouter(tags=["IPOs"])


# Dependency injection
async def get_ipo_repo():
    async with get_db_session() as session:
        yield SQLIPORepository(session)


async def get_company_repo():
    async with get_db_session() as session:
        yield SQLCompanyRepository(session)


async def get_financial_repo():
    from app.infrastructure.repositories.sql_repositories import SQLFinancialRepository
    async with get_db_session() as session:
        yield SQLFinancialRepository(session)


async def get_discover_use_case():
    async with get_db_session() as session:
        yield DiscoverIPOsUseCase(SQLIPORepository(session), SQLCompanyRepository(session))


async def get_details_use_case(
    ipo_repo=Depends(get_ipo_repo),
):
    return GetIPODetailsUseCase(ipo_repo)


async def get_list_use_case(ipo_repo=Depends(get_ipo_repo)):
    return ListUpcomingIPOsUseCase(ipo_repo)


async def get_search_use_case(ipo_repo=Depends(get_ipo_repo)):
    return SearchIPOsUseCase(ipo_repo)


async def get_recent_use_case(ipo_repo=Depends(get_ipo_repo)):
    return GetRecentlyListedIPOsUseCase(ipo_repo)


async def get_create_use_case(
    ipo_repo=Depends(get_ipo_repo),
    company_repo=Depends(get_company_repo),
):
    return CreateIPOUseCase(ipo_repo, company_repo)


async def get_update_status_use_case(ipo_repo=Depends(get_ipo_repo)):
    return UpdateIPOStatusUseCase(ipo_repo)


async def get_company_profile_use_case(company_repo=Depends(get_company_repo)):
    return GetCompanyProfileUseCase(company_repo)


async def get_create_company_use_case(company_repo=Depends(get_company_repo)):
    return CreateCompanyProfileUseCase(company_repo)


async def get_list_by_sector_use_case(company_repo=Depends(get_company_repo)):
    return ListCompaniesBySectorUseCase(company_repo)


async def get_list_by_industry_use_case(company_repo=Depends(get_company_repo)):
    return ListCompaniesByIndustryUseCase(company_repo)


# Request/Response models
from pydantic import BaseModel, Field
from typing import Optional


class IPOSymbolRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, pattern="^[A-Z0-9.]+$")


class IPOCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, pattern="^[A-Z0-9.]+$")
    company_name: str = Field(..., min_length=1, max_length=255)
    exchange: Exchange
    sector: Sector = Sector.UNCLASSIFIED
    industry: Industry = Industry.OTHER
    status: IPOStatus = IPOStatus.ANNOUNCED
    expected_date: Optional[datetime] = None
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    shares_offered: Optional[int] = None
    underwriters: List[str] = []
    use_of_proceeds: str = ""
    prospectus_url: str = ""


class IPOStatusUpdateRequest(BaseModel):
    status: IPOStatus


class CompanyProfileRequest(BaseModel):
    legal_name: str
    common_name: str
    description: str = ""
    business_model: str = ""
    sector: Sector
    industry: Industry
    headquarters: str = ""
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    website: str = ""
    ceo: str = ""
    cfo: str = ""
    chairman: str = ""
    board_members: List[str] = []
    major_shareholders: dict = {}
    competitors: List[str] = []
    competitive_advantages: List[str] = []
    risk_factors: List[str] = []
    key_products: List[str] = []
    target_markets: List[str] = []
    regulatory_environment: str = ""
    esg_score: Optional[float] = None


class IPORResponse(BaseModel):
    symbol: str
    company_name: str
    exchange: str
    sector: str
    industry: str
    status: str
    expected_date: Optional[datetime] = None
    listed_date: Optional[datetime] = None
    price_range: Optional[dict] = None
    shares_offered: Optional[int] = None
    valuation: Optional[dict] = None
    underwriters: List[str] = []
    lead_underwriter: str = ""
    # Issue details
    issue_size: Optional[float] = None
    face_value: Optional[float] = None
    lot_size: Optional[int] = None
    registrar: Optional[str] = None
    # Source attribution
    source: Optional[str] = None
    source_reference: Optional[str] = None
    source_updated_at: Optional[datetime] = None
    collector_version: Optional[str] = None
    data_quality_score: Optional[float] = None
    last_verified_at: Optional[datetime] = None
    # Data freshness
    data_age_days: Optional[int] = None
    source_age_days: Optional[int] = None


class FinancialPeriodResponse(BaseModel):
    period: Optional[str] = None
    period_end: Optional[datetime] = None
    revenue: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_income: Optional[float] = None
    operating_margin: Optional[float] = None
    net_income: Optional[float] = None
    net_margin: Optional[float] = None
    ebitda: Optional[float] = None
    free_cash_flow: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_debt: Optional[float] = None
    total_equity: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None


class FinancialHistoryResponse(BaseModel):
    symbol: str
    periods: List[FinancialPeriodResponse] = []


class CompanyProfileResponse(BaseModel):
    legal_name: str
    common_name: str
    description: str
    business_model: str
    sector: str
    industry: str
    headquarters: str
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    website: str
    ceo: str
    cfo: str
    chairman: str
    board_members: List[str] = []
    major_shareholders: dict = {}
    competitors: List[str] = []
    competitive_advantages: List[str] = []
    risk_factors: List[str] = []
    key_products: List[str] = []
    target_markets: List[str] = []
    regulatory_environment: str = ""
    esg_score: Optional[float] = None


@router.post("/discover", response_model=List[IPORResponse])
async def discover_ipos(
    lookahead_days: int = Query(90, ge=1, le=365),
    sources: List[str] = Query(["nasdaq", "nyse", "sec", "renaissance", "investorgain"]),
    min_market_cap: float = Query(0, ge=0),
    use_case: DiscoverIPOsUseCase = Depends(get_discover_use_case),
):
    """Discover upcoming IPOs from multiple sources."""
    ipos = await use_case.execute(
        lookahead_days=lookahead_days,
        sources=sources,
        min_market_cap=min_market_cap,
    )
    return [_ipo_to_response(ipo) for ipo in ipos]


@router.get("/upcoming", response_model=List[IPORResponse])
async def list_upcoming_ipos(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    exchange: Optional[Exchange] = Query(None),
    sector: Optional[Sector] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    region: Optional[str] = Query(None, pattern="^(india|foreign)$"),
    phase: Optional[str] = Query(None, pattern="^(upcoming|current|listed)$"),
    min_quality_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum data quality score (0-1)"),
    require_source: bool = Query(True, description="Only return IPOs with source attribution"),
    use_case: ListUpcomingIPOsUseCase = Depends(get_list_use_case),
):
    """List upcoming IPOs with filters.

    - region: "india" (NSE/BSE) or "foreign" (all other exchanges)
    - phase: "upcoming" (not yet open), "current" (bidding started, not
      yet listed), or "listed" (already listed)
    - min_quality_score: Minimum data quality score (0-1)
    - require_source: Only return IPOs with source attribution
    """
    ipos = await use_case.execute(
        limit=limit,
        offset=offset,
        status=status,
        exchange=exchange,
        sector=sector,
        from_date=from_date,
        to_date=to_date,
        region=region,
        phase=phase,
    )
    
    # Apply data quality gate
    filtered_ipos = []
    for ipo in ipos:
        # Check source attribution requirement
        if require_source and not ipo.source:
            continue
        
        # Check minimum quality score
        if ipo.data_quality_score is not None and ipo.data_quality_score < min_quality_score:
            continue
            
        filtered_ipos.append(ipo)
    
    return [_ipo_to_response(ipo) for ipo in filtered_ipos]


@router.get("/upcoming/count", response_model=int)
async def count_upcoming_ipos(
    status: Optional[str] = Query(None),
    exchange: Optional[Exchange] = Query(None),
    sector: Optional[Sector] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    region: Optional[str] = Query(None, pattern="^(india|foreign)$"),
    phase: Optional[str] = Query(None, pattern="^(upcoming|current|listed)$"),
    use_case: ListUpcomingIPOsUseCase = Depends(get_list_use_case),
):
    """Get total count of upcoming IPOs with filters for pagination."""
    # The use case doesn't have a count method yet, so we'll return 0 for now
    # This would need to be implemented in the use case and repository
    return 0


@router.get("/recent", response_model=List[IPORResponse])
async def get_recently_listed(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    use_case: GetRecentlyListedIPOsUseCase = Depends(get_recent_use_case),
):
    """Get recently listed IPOs."""
    ipos = await use_case.execute(days=days, limit=limit)
    return [_ipo_to_response(ipo) for ipo in ipos]


@router.get("/search", response_model=List[IPORResponse])
async def search_ipos(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    use_case: SearchIPOsUseCase = Depends(get_search_use_case),
):
    """Search IPOs by symbol or company name."""
    ipos = await use_case.execute(query=q, limit=limit)
    return [_ipo_to_response(ipo) for ipo in ipos]


@router.get("/financials/{symbol}", response_model=FinancialHistoryResponse)
async def get_financial_history(
    symbol: str,
    periods: int = Query(8, ge=1, le=40),
    financial_repo=Depends(get_financial_repo),
):
    """Get financial statement history for a symbol."""
    from app.domain.value_objects.value_objects import Money, Percentage, Ratio

    def amount(value):
        return float(value.amount) if isinstance(value, Money) and value else (None if value is None else float(value))

    def pct(value):
        return float(value.to_decimal()) if isinstance(value, Percentage) and value else (None if value is None else float(value))

    def ratio(value):
        return float(value.value) if isinstance(value, Ratio) and value else (None if value is None else float(value))

    metrics = await financial_repo.get_history(symbol.upper(), periods=periods)
    periods_data = []
    for m in metrics:
        periods_data.append(
            FinancialPeriodResponse(
                period=getattr(m, "period", None),
                period_end=m.as_of_date if hasattr(m, "as_of_date") and m.as_of_date else None,
                revenue=amount(m.revenue),
                revenue_growth_yoy=pct(m.revenue_growth_yoy),
                gross_profit=amount(m.gross_profit),
                gross_margin=pct(m.gross_margin),
                operating_income=amount(m.operating_income),
                operating_margin=pct(m.operating_margin),
                net_income=amount(m.net_income),
                net_margin=pct(m.net_margin),
                ebitda=amount(m.ebitda),
                free_cash_flow=amount(m.free_cash_flow),
                cash_and_equivalents=amount(m.cash_and_equivalents),
                total_debt=amount(m.total_debt),
                total_equity=amount(m.total_equity),
                debt_to_equity=ratio(m.debt_to_equity),
                current_ratio=ratio(m.current_ratio),
                roe=pct(m.roe),
                roic=pct(m.roic),
            )
        )
    return FinancialHistoryResponse(symbol=symbol.upper(), periods=periods_data)


@router.get("/{symbol}", response_model=IPORResponse)
async def get_ipo_details(
    symbol: str,
    use_case: GetIPODetailsUseCase = Depends(get_details_use_case),
):
    """Get IPO details by symbol."""
    ipo = await use_case.execute(symbol.upper())
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO not found: {symbol}")
    return _ipo_to_response(ipo)


@router.post("", response_model=IPORResponse, status_code=status.HTTP_201_CREATED)
async def create_ipo(
    request: IPOCreateRequest,
    use_case: CreateIPOUseCase = Depends(get_create_use_case),
):
    """Create a new IPO entry."""
    from app.domain.value_objects.value_objects import Money, PriceRange
    from app.domain.value_objects.value_objects import IPODetails
    
    price_range = None
    if request.price_range_low and request.price_range_high:
        price_range = PriceRange(
            low=Money(request.price_range_low, "USD"),
            high=Money(request.price_range_high, "USD"),
        )
    
    ipo = IPODetails(
        symbol=request.symbol.upper(),
        company_name=request.company_name,
        exchange=request.exchange,
        sector=request.sector,
        industry=request.industry,
        status=request.status,
        expected_date=request.expected_date,
        price_range=price_range,
        shares_offered=request.shares_offered,
        underwriters=request.underwriters,
        use_of_proceeds=request.use_of_proceeds,
        prospectus_url=request.prospectus_url,
    )
    
    created = await use_case.execute(ipo)
    return _ipo_to_response(created)


@router.patch("/{symbol}/status", response_model=IPORResponse)
async def update_ipo_status(
    symbol: str,
    request: IPOStatusUpdateRequest,
    use_case: UpdateIPOStatusUseCase = Depends(get_update_status_use_case),
):
    """Update IPO status."""
    success = await use_case.execute(symbol.upper(), request.status.value)
    if not success:
        raise HTTPException(status_code=404, detail=f"IPO not found: {symbol}")
    
    # Return updated IPO
    from app.application.use_cases.ipo_use_cases import GetIPODetailsUseCase
    from app.infrastructure.repositories.sql_repositories import SQLIPORepository
    from app.infrastructure.database.session import get_db_session
    
    async with get_db_session() as session:
        repo = SQLIPORepository(session)
        get_use_case = GetIPODetailsUseCase(repo, None)
        ipo = await get_use_case.execute(symbol.upper())
        return _ipo_to_response(ipo)


@router.get("/companies/{symbol}", response_model=CompanyProfileResponse)
async def get_company_profile(
    symbol: str,
    use_case: GetCompanyProfileUseCase = Depends(get_company_profile_use_case),
):
    """Get company profile by symbol."""
    profile = await use_case.execute(symbol.upper())
    if not profile:
        raise HTTPException(status_code=404, detail=f"Company not found: {symbol}")
    return _company_to_response(profile)


@router.post("/companies", response_model=CompanyProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    request: CompanyProfileRequest,
    use_case: CreateCompanyProfileUseCase = Depends(get_create_company_use_case),
):
    """Create a new company profile."""
    from app.domain.value_objects.value_objects import CompanyProfile
    
    company = CompanyProfile(**request.model_dump())
    created = await use_case.execute(company)
    return _company_to_response(created)


@router.get("/companies/sector/{sector}", response_model=List[CompanyProfileResponse])
async def list_companies_by_sector(
    sector: Sector,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    use_case: ListCompaniesBySectorUseCase = Depends(get_list_by_sector_use_case),
):
    """List companies by sector."""
    companies = await use_case.execute(sector=sector, limit=limit, offset=offset)
    return [_company_to_response(c) for c in companies]


@router.get("/companies/industry/{industry}", response_model=List[CompanyProfileResponse])
async def list_companies_by_industry(
    industry: Industry,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    use_case: ListCompaniesByIndustryUseCase = Depends(get_list_by_industry_use_case),
):
    """List companies by industry."""
    companies = await use_case.execute(industry=industry, limit=limit, offset=offset)
    return [_company_to_response(c) for c in companies]


def _ipo_to_response(ipo) -> IPORResponse:
    """Convert IPO entity to response model."""
    now = datetime.utcnow().replace(tzinfo=None)  # Ensure offset-naive
    
    # Calculate data age
    data_age_days = None
    if ipo.created_at:
        created_at = ipo.created_at
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)
        data_age_days = (now - created_at).days
    
    # Calculate source age
    source_age_days = None
    if ipo.source_updated_at:
        source_updated = ipo.source_updated_at
        if source_updated.tzinfo is not None:
            source_updated = source_updated.replace(tzinfo=None)
        source_age_days = (now - source_updated).days
    
    # Extract price range from price_range attribute
    price_range = None
    if ipo.price_range:
        price_range = {
            "low": float(ipo.price_range.low.amount) if ipo.price_range.low else None,
            "high": float(ipo.price_range.high.amount) if ipo.price_range.high else None,
        }
    
    return IPORResponse(
        symbol=ipo.symbol,
        company_name=ipo.company_name,
        exchange=ipo.exchange.value if hasattr(ipo.exchange, 'value') else ipo.exchange,
        sector=ipo.sector.value if hasattr(ipo.sector, 'value') else ipo.sector,
        industry=ipo.industry.value if hasattr(ipo.industry, 'value') else ipo.industry,
        status=ipo.status.value if hasattr(ipo.status, 'value') else ipo.status,
        expected_date=ipo.expected_date,
        listed_date=ipo.listed_date,
        price_range=price_range,
        shares_offered=ipo.shares_offered,
        valuation={
            "enterprise_value": float(ipo.valuation.enterprise_value.amount) if ipo.valuation else None,
            "equity_value": float(ipo.valuation.equity_value.amount) if ipo.valuation else None,
        } if ipo.valuation else None,
        underwriters=ipo.underwriters,
        lead_underwriter=ipo.lead_underwriter,
        issue_size=float(ipo.issue_size.amount) if ipo.issue_size else None,
        face_value=float(ipo.face_value.amount) if ipo.face_value else None,
        lot_size=ipo.lot_size,
        registrar=ipo.registrar,
        source=ipo.source if ipo.source else None,
        source_reference=ipo.source_reference if ipo.source_reference else None,
        source_updated_at=ipo.source_updated_at,
        collector_version=ipo.collector_version if ipo.collector_version else None,
        data_quality_score=ipo.data_quality_score if ipo.data_quality_score else None,
        last_verified_at=ipo.last_verified_at,
        data_age_days=data_age_days,
        source_age_days=source_age_days,
    )


def _company_to_response(company) -> CompanyProfileResponse:
    """Convert company entity to response model."""
    return CompanyProfileResponse(
        legal_name=company.legal_name,
        common_name=company.common_name,
        description=company.description,
        business_model=company.business_model,
        sector=company.sector.value if hasattr(company.sector, 'value') else company.sector,
        industry=company.industry.value if hasattr(company.industry, 'value') else company.industry,
        headquarters=company.headquarters,
        founded_year=company.founded_year,
        employee_count=company.employee_count,
        website=company.website,
        ceo=company.ceo,
        cfo=company.cfo,
        chairman=company.chairman,
        board_members=company.board_members,
        major_shareholders=company.major_shareholders,
        competitors=company.competitors,
        competitive_advantages=company.competitive_advantages,
        risk_factors=company.risk_factors,
        key_products=company.key_products,
        target_markets=company.target_markets,
        regulatory_environment=company.regulatory_environment,
        esg_score=company.esg_score,
    )