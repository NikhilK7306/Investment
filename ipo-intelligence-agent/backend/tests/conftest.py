#!/usr/bin/env python
"""Test configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.infrastructure.database.models import Base
from app.core.config.settings import get_settings


# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_ipo_data():
    """Sample IPO data for testing."""
    return {
        "symbol": "TEST",
        "company_name": "Test Company Inc",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "industry": "Software",
        "expected_date": datetime(2024, 3, 15),
        "price_range_low": 18.00,
        "price_range_high": 22.00,
        "shares_offered": 10000000,
        "status": "FILED",
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "legal_name": "Test Company Inc",
        "common_name": "TestCo",
        "ticker": "TEST",
        "description": "A test company for unit testing",
        "business_model": "SaaS",
        "sector": "Technology",
        "industry": "Software",
        "headquarters": "San Francisco, CA, USA",
        "website": "https://testco.com",
        "ceo": "John Doe",
        "cfo": "Jane Smith",
        "employee_count": 500,
        "founded_year": 2015,
    }


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        "revenue": 100_000_000,
        "revenue_growth_yoy": 0.25,
        "gross_profit": 75_000_000,
        "gross_margin": 0.75,
        "operating_income": 15_000_000,
        "operating_margin": 0.15,
        "net_income": 10_000_000,
        "net_margin": 0.10,
        "ebitda": 20_000_000,
        "ebitda_margin": 0.20,
        "free_cash_flow": 12_000_000,
        "fcf_margin": 0.12,
        "total_assets": 200_000_000,
        "total_liabilities": 80_000_000,
        "total_equity": 120_000_000,
        "cash_and_equivalents": 50_000_000,
        "total_debt": 30_000_000,
        "debt_to_equity": 0.25,
        "current_ratio": 2.5,
        "quick_ratio": 2.0,
        "roe": 0.083,
        "roa": 0.05,
        "roic": 0.12,
    }


# Mock fixtures for external services
@pytest.fixture
def mock_yfinance_data():
    """Mock yfinance data."""
    return {
        "info": {
            "symbol": "TEST",
            "longName": "Test Company Inc",
            "sector": "Technology",
            "industry": "Software",
            "marketCap": 2_000_000_000,
            "enterpriseValue": 1_950_000_000,
            "trailingPE": 25.5,
            "forwardPE": 22.1,
            "priceToSalesTrailing12Months": 8.2,
            "enterpriseToRevenue": 7.8,
            "enterpriseToEbitda": 18.5,
            "profitMargins": 0.15,
            "revenueGrowth": 0.25,
        }
    }


@pytest.fixture
def mock_news_data():
    """Mock news data."""
    return [
        {
            "title": "TestCo Announces Strong Q4 Results",
            "content": "Test Company Inc reported revenue of $100M...",
            "source": "Bloomberg",
            "published_at": "2024-01-15T10:00:00Z",
            "sentiment": 0.6,
        },
        {
            "title": "Analyst Upgrades TestCo to Buy",
            "content": "Goldman Sachs upgraded TestCo...",
            "source": "Reuters",
            "published_at": "2024-01-14T14:30:00Z",
            "sentiment": 0.8,
        },
    ]


# Async test helpers
class AsyncTestClient:
    """Async test client helper."""
    
    def __init__(self, app):
        self.app = app
    
    async def get(self, url: str, **kwargs):
        from httpx import AsyncClient
        async with AsyncClient(app=self.app, base_url="http://test") as client:
            return await client.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs):
        from httpx import AsyncClient
        async with AsyncClient(app=self.app, base_url="http://test") as client:
            return await client.post(url, **kwargs)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring API key"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add unit marker by default
        if not any(marker.name in ("unit", "integration", "slow") for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)