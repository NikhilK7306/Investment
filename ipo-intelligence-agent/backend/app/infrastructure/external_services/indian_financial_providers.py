"""Indian financial data providers for listed and pre-IPO companies."""

import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.domain.value_objects.value_objects import Money, Percentage, Ratio
from app.infrastructure.external_services.providers import (
    FinancialDataProvider,
    ProviderConfig,
    ProviderResult,
)


class FMPIndianProvider(FinancialDataProvider):
    """Financial Modeling Prep provider for Indian stocks (NSE/BSE)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        config = ProviderConfig(
            name="fmp_indian",
            base_url="https://financialmodelingprep.com/api/v3",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=30 if self.api_key else 0,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    def _get_symbol_variants(self, symbol: str) -> List[str]:
        """Generate NSE/BSE symbol variants for FMP."""
        base = symbol.upper().replace(".NS", "").replace(".BO", "")
        return [
            f"{base}.NS",
            f"{base}.BO",
            base,
        ]

    async def _check_health(self) -> None:
        if not self.api_key:
            raise Exception("FMP API key not configured")
        client = await self._get_client()
        response = await client.get(
            "/profile/AAPL",
            params={"apikey": self.api_key},
            timeout=10.0,
        )
        if response.status_code not in (200, 404):
            raise Exception(f"FMP returned {response.status_code}")

    async def fetch_financials(
        self,
        symbol: str,
        periods: int = 8,
    ) -> ProviderResult[Dict[str, Any]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="FMP API key not configured",
                error_type="MISSING_API_KEY",
            )

        try:
            client = await self._get_client()
            variants = self._get_symbol_variants(symbol)
            
            for variant in variants:
                # Try income statement
                income_response = await client.get(
                    f"/income-statement/{variant}",
                    params={"period": "quarter", "limit": periods, "apikey": self.api_key},
                    timeout=30.0,
                )
                
                if income_response.status_code == 200:
                    income_data = income_response.json()
                    if income_data:
                        return await self._build_financial_result(client, variant, income_data, periods)
            
            return ProviderResult(
                success=False,
                error=f"No financial data found for {symbol} on NSE/BSE",
                error_type="NOT_FOUND",
                source="financialmodelingprep.com",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="financialmodelingprep.com",
            )

    async def _build_financial_result(
        self,
        client: httpx.AsyncClient,
        variant: str,
        income_data: List[Dict],
        periods: int,
    ) -> ProviderResult[Dict[str, Any]]:
        # Fetch balance sheet
        bs_response = await client.get(
            f"/balance-sheet-statement/{variant}",
            params={"period": "quarter", "limit": periods, "apikey": self.api_key},
            timeout=30.0,
        )
        balance_sheet = bs_response.json() if bs_response.status_code == 200 else []

        # Fetch cash flow
        cf_response = await client.get(
            f"/cash-flow-statement/{variant}",
            params={"period": "quarter", "limit": periods, "apikey": self.api_key},
            timeout=30.0,
        )
        cash_flow = cf_response.json() if cf_response.status_code == 200 else []

        # Fetch key metrics
        metrics_response = await client.get(
            f"/key-metrics/{variant}",
            params={"period": "quarter", "limit": periods, "apikey": self.api_key},
            timeout=30.0,
        )
        key_metrics = metrics_response.json() if metrics_response.status_code == 200 else []

        # Fetch ratios
        ratios_response = await client.get(
            f"/ratios/{variant}",
            params={"period": "quarter", "limit": periods, "apikey": self.api_key},
            timeout=30.0,
        )
        ratios = ratios_response.json() if ratios_response.status_code == 200 else []

        # Build structured financial statements
        statements = []
        for i in range(min(periods, len(income_data))):
            income = income_data[i] if i < len(income_data) else {}
            bs = balance_sheet[i] if i < len(balance_sheet) else {}
            cf = cash_flow[i] if i < len(cash_flow) else {}
            km = key_metrics[i] if i < len(key_metrics) else {}
            rat = ratios[i] if i < len(ratios) else {}

            period_end = income.get("date") or bs.get("date") or cf.get("date")
            
            stmt = {
                "period_end": period_end,
                "period_type": "quarterly",
                "revenue": income.get("revenue"),
                "gross_profit": income.get("grossProfit"),
                "operating_income": income.get("operatingIncome"),
                "net_income": income.get("netIncome"),
                "ebitda": income.get("ebitda"),
                "total_assets": bs.get("totalAssets"),
                "total_liabilities": bs.get("totalLiabilities"),
                "total_equity": bs.get("totalStockholdersEquity"),
                "cash_and_equivalents": bs.get("cashAndCashEquivalents"),
                "total_debt": bs.get("totalDebt"),
                "operating_cash_flow": cf.get("operatingCashFlow"),
                "free_cash_flow": cf.get("freeCashFlow"),
                "capex": cf.get("capitalExpenditure"),
                "gross_margin": income.get("grossProfit", 0) / income.get("revenue", 1) if income.get("revenue") else None,
                "operating_margin": income.get("operatingIncome", 0) / income.get("revenue", 1) if income.get("revenue") else None,
                "net_margin": income.get("netIncome", 0) / income.get("revenue", 1) if income.get("revenue") else None,
                "ebitda_margin": income.get("ebitda", 0) / income.get("revenue", 1) if income.get("revenue") else None,
                "debt_to_equity": bs.get("totalDebt", 0) / bs.get("totalStockholdersEquity", 1) if bs.get("totalStockholdersEquity") else None,
                "current_ratio": bs.get("totalCurrentAssets", 0) / bs.get("totalCurrentLiabilities", 1) if bs.get("totalCurrentLiabilities") else None,
                "quick_ratio": (bs.get("totalCurrentAssets", 0) - bs.get("inventory", 0)) / bs.get("totalCurrentLiabilities", 1) if bs.get("totalCurrentLiabilities") else None,
                "roe": rat.get("returnOnEquity"),
                "roa": rat.get("returnOnAssets"),
                "roic": rat.get("returnOnCapitalEmployed"),
                "revenue_growth_yoy": km.get("revenueGrowth"),
                "fcf_margin": cf.get("freeCashFlow", 0) / income.get("revenue", 1) if income.get("revenue") else None,
            }
            statements.append(stmt)

        return ProviderResult(
            success=True,
            data={
                "statements": statements,
                "symbol_used": variant,
                "periods": len(statements),
            },
            source="financialmodelingprep.com",
            source_reference=f"https://financialmodelingprep.com/api/v3/income-statement/{variant}",
        )

    async def fetch_company_profile(
        self,
        symbol: str,
    ) -> ProviderResult[Dict[str, Any]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="FMP API key not configured",
                error_type="MISSING_API_KEY",
            )

        try:
            client = await self._get_client()
            variants = self._get_symbol_variants(symbol)
            
            for variant in variants:
                response = await client.get(
                    f"/profile/{variant}",
                    params={"apikey": self.api_key},
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        profile = data[0]
                        return ProviderResult(
                            success=True,
                            data={
                                "legal_name": profile.get("companyName"),
                                "ticker": profile.get("symbol"),
                                "exchange": "NSE" if ".NS" in variant else "BSE",
                                "sector": profile.get("sector"),
                                "industry": profile.get("industry"),
                                "description": profile.get("description"),
                                "website": profile.get("website"),
                                "ceo": profile.get("ceo"),
                                "employees": profile.get("fullTimeEmployees"),
                                "headquarters": profile.get("headquarter"),
                                "market_cap": profile.get("mktCap"),
                                "price": profile.get("price"),
                            },
                            source="financialmodelingprep.com",
                            source_reference=f"https://financialmodelingprep.com/api/v3/profile/{variant}",
                        )
            
            return ProviderResult(
                success=False,
                error=f"Company profile not found for {symbol}",
                error_type="NOT_FOUND",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="financialmodelingprep.com",
            )

    async def fetch_drhp_financials(
        self,
        symbol: str,
        company_name: str,
        ipo_details: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult[Dict[str, Any]]:
        """FMP doesn't provide pre-IPO DRHP financials."""
        return ProviderResult(
            success=False,
            error="FMP does not provide pre-IPO DRHP financials",
            error_type="NOT_SUPPORTED",
            source="financialmodelingprep.com",
        )


class AlphaVantageIndianProvider(FinancialDataProvider):
    """Alpha Vantage provider for Indian stocks."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        config = ProviderConfig(
            name="alphavantage_indian",
            base_url="https://www.alphavantage.co",
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=5 if self.api_key else 0,
            headers={"User-Agent": "IPO Intelligence Agent/1.0"},
        )
        super().__init__(config)

    def _get_symbol_variants(self, symbol: str) -> List[str]:
        base = symbol.upper().replace(".NS", "").replace(".BO", "")
        return [
            f"{base}.BSE",
            f"{base}.NSE",
            base,
        ]

    async def _check_health(self) -> None:
        if not self.api_key:
            raise Exception("Alpha Vantage API key not configured")
        client = await self._get_client()
        response = await client.get(
            "/query",
            params={"function": "OVERVIEW", "symbol": "RELIANCE.BSE", "apikey": self.api_key},
            timeout=10.0,
        )
        if response.status_code not in (200, 404):
            raise Exception(f"Alpha Vantage returned {response.status_code}")

    async def fetch_financials(
        self,
        symbol: str,
        periods: int = 8,
    ) -> ProviderResult[Dict[str, Any]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="Alpha Vantage API key not configured",
                error_type="MISSING_API_KEY",
            )

        try:
            client = await self._get_client()
            variants = self._get_symbol_variants(symbol)
            
            for variant in variants:
                # Alpha Vantage has limited financial data - mainly overview
                response = await client.get(
                    "/query",
                    params={
                        "function": "INCOME_STATEMENT",
                        "symbol": variant,
                        "apikey": self.api_key,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "quarterlyReports" in data and data["quarterlyReports"]:
                        return self._parse_av_financials(data, variant)
            
            return ProviderResult(
                success=False,
                error=f"No financial data found for {symbol}",
                error_type="NOT_FOUND",
                source="alphavantage.co",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="alphavantage.co",
            )

    def _parse_av_financials(self, data: Dict, variant: str) -> ProviderResult[Dict[str, Any]]:
        reports = data.get("quarterlyReports", [])
        statements = []
        
        for report in reports[:8]:
            stmt = {
                "period_end": report.get("fiscalDateEnding"),
                "period_type": "quarterly",
                "revenue": self._safe_float(report.get("totalRevenue")),
                "gross_profit": self._safe_float(report.get("grossProfit")),
                "operating_income": self._safe_float(report.get("operatingIncome")),
                "net_income": self._safe_float(report.get("netIncome")),
                "ebitda": self._safe_float(report.get("ebitda")),
                "total_assets": None,  # Not in income statement
                "total_liabilities": None,
                "total_equity": None,
                "cash_and_equivalents": None,
                "total_debt": None,
                "operating_cash_flow": None,
                "free_cash_flow": None,
                "capex": None,
            }
            statements.append(stmt)

        return ProviderResult(
            success=True,
            data={
                "statements": statements,
                "symbol_used": variant,
                "periods": len(statements),
            },
            source="alphavantage.co",
            source_reference=f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={variant}",
        )

    def _safe_float(self, val: Any) -> Optional[float]:
        if val is None or val == "None" or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    async def fetch_company_profile(
        self,
        symbol: str,
    ) -> ProviderResult[Dict[str, Any]]:
        if not self.api_key:
            return ProviderResult(
                success=False,
                error="Alpha Vantage API key not configured",
                error_type="MISSING_API_KEY",
            )

        try:
            client = await self._get_client()
            variants = self._get_symbol_variants(symbol)
            
            for variant in variants:
                response = await client.get(
                    "/query",
                    params={
                        "function": "OVERVIEW",
                        "symbol": variant,
                        "apikey": self.api_key,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and "Symbol" in data:
                        return ProviderResult(
                            success=True,
                            data={
                                "legal_name": data.get("Name"),
                                "ticker": data.get("Symbol"),
                                "exchange": "BSE" if ".BSE" in variant else "NSE",
                                "sector": data.get("Sector"),
                                "industry": data.get("Industry"),
                                "description": data.get("Description"),
                                "website": None,
                                "ceo": None,
                                "employees": self._safe_int(data.get("FullTimeEmployees")),
                                "headquarters": f"{data.get('Address', '')}, {data.get('City', '')}, {data.get('State', '')}, {data.get('Country', '')}".strip(", "),
                                "market_cap": self._safe_float(data.get("MarketCapitalization")),
                                "price": self._safe_float(data.get("LatestPrice")),
                            },
                            source="alphavantage.co",
                            source_reference=f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={variant}",
                        )
            
            return ProviderResult(
                success=False,
                error=f"Company profile not found for {symbol}",
                error_type="NOT_FOUND",
            )
            
        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                error_type="PARSE_ERROR",
                source="alphavantage.co",
            )

    def _safe_int(self, val: Any) -> Optional[int]:
        if val is None or val == "None" or val == "":
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    async def fetch_drhp_financials(
        self,
        symbol: str,
        company_name: str,
        ipo_details: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult[Dict[str, Any]]:
        """Alpha Vantage doesn't provide pre-IPO DRHP financials."""
        return ProviderResult(
            success=False,
            error="Alpha Vantage does not provide pre-IPO DRHP financials",
            error_type="NOT_SUPPORTED",
            source="alphavantage.co",
        )


class DRHPDocumentProvider(FinancialDataProvider):
    """Provider for extracting financials from DRHP/RHP documents for pre-IPO companies."""

    def __init__(self):
        config = ProviderConfig(
            name="drhp_document",
            base_url="https://www.sebi.gov.in",
            timeout_seconds=60,
            max_retries=3,
            rate_limit_per_minute=10,
            headers={
                "User-Agent": "IPO Intelligence Research dev@example.com",
                "Accept": "application/pdf, text/html",
            },
        )
        super().__init__(config)
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=self.config.headers,
                follow_redirects=True,
            )
        return self._http_client

    async def _check_health(self) -> None:
        client = await self._get_client()
        response = await client.get("/sebiweb/home/list/3/4/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/P/0?type=3&category=4", timeout=10.0)
        if response.status_code not in (200, 404):
            raise Exception(f"SEBI returned {response.status_code}")

    async def close(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def fetch_financials(
        self,
        symbol: str,
        periods: int = 8,
    ) -> ProviderResult[Dict[str, Any]]:
        """Not applicable for DRHP provider - use fetch_drhp_financials instead."""
        return ProviderResult(
            success=False,
            error="Use fetch_drhp_financials for DRHP extraction",
            error_type="WRONG_METHOD",
        )

    async def fetch_company_profile(
        self,
        symbol: str,
    ) -> ProviderResult[Dict[str, Any]]:
        """Not applicable for DRHP provider."""
        return ProviderResult(
            success=False,
            error="Use fetch_drhp_financials for DRHP extraction",
            error_type="WRONG_METHOD",
        )

    async def fetch_drhp_financials(
        self,
        symbol: str,
        company_name: str,
        ipo_details: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult[Dict[str, Any]]:
        """Extract financial data from DRHP/RHP PDF for pre-IPO companies."""
        try:
            # First, find the DRHP/RHP URL for this company
            drhp_url = await self._find_drhp_url(symbol, company_name, ipo_details)
            
            if not drhp_url:
                return ProviderResult(
                    success=False,
                    error=f"Could not find DRHP/RHP for {symbol} ({company_name})",
                    error_type="DOCUMENT_NOT_FOUND",
                    source="sebi.gov.in / nseindia.com / bseindia.com",
                )

            # Download and extract text from PDF
            pdf_text = await self._download_and_extract_pdf(drhp_url)
            
            if not pdf_text:
                return ProviderResult(
                    success=False,
                    error="Failed to extract text from DRHP/RHP PDF",
                    error_type="PDF_EXTRACTION_FAILED",
                    source=drhp_url,
                )

            # Extract financial statements from text
            financials = self._extract_financials_from_text(pdf_text, company_name)
            
            if not financials.get("statements"):
                return ProviderResult(
                    success=False,
                    error="No financial data found in DRHP/RHP document",
                    error_type="NO_FINANCIAL_DATA_IN_DOC",
                    source=drhp_url,
                )

            return ProviderResult(
                success=True,
                data={
                    "statements": financials["statements"],
                    "source_document": drhp_url,
                    "extraction_method": "pdf_text_parsing",
                    "periods": len(financials["statements"]),
                },
                source="drhp_document",
                source_reference=drhp_url,
            )

        except Exception as e:
            return ProviderResult(
                success=False,
                error=f"DRHP extraction failed: {str(e)}",
                error_type="EXTRACTION_ERROR",
                source="drhp_document",
            )

    async def _find_drhp_url(
        self,
        symbol: str,
        company_name: str,
        ipo_details: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Find DRHP/RHP document URL from SEBI, NSE, or BSE."""
        # Try ipo_details first
        if ipo_details and ipo_details.get("prospectus_url"):
            return ipo_details["prospectus_url"]
        
        # Try SEBI search
        client = await self._get_client()
        
        # Search SEBI EDGAR-style index
        try:
            response = await client.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={
                    "q": f'"{company_name}" DRHP',
                    "forms": "DRHP,RHP",
                    "dateRange": "y",
                },
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                for hit in hits:
                    src = hit.get("_source", {})
                    if company_name.lower() in str(src.get("display_names", [""])[0]).lower():
                        ciks = src.get("ciks") or []
                        adsh = str(src.get("adsh", "")).replace("-", "")
                        if ciks and adsh:
                            return f"https://www.sec.gov/Archives/edgar/data/{ciks[0]}/{adsh}/"
        except Exception:
            pass

        # Try NSE
        try:
            response = await client.get(
                "https://www.nseindia.com/api/ipo-documents",
                params={"symbol": symbol},
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                for doc in data.get("documents", []):
                    if "drhp" in doc.get("name", "").lower() or "rhp" in doc.get("name", "").lower():
                        return doc.get("url")
        except Exception:
            pass

        # Try BSE
        try:
            response = await client.get(
                "https://api.bseindia.com/BseIndiaAPI/api/AnnouncementGet/w",
                params={"strCat": "IPO", "strPrevDate": "", "strScrip": symbol, "strSearch": "P", "strToDate": "", "strType": "C"},
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                # Parse BSE announcements for DRHP/RHP
                for item in data.get("Table", []):
                    if "drhp" in str(item.get("NEWSSUB", "")).lower() or "rhp" in str(item.get("NEWSSUB", "")).lower():
                        return item.get("ATTACHMENTNAME") or item.get("PDFPATH")
        except Exception:
            pass

        return None

    async def _download_and_extract_pdf(self, url: str) -> Optional[str]:
        """Download PDF and extract text."""
        try:
            client = await self._get_client()
            response = await client.get(url, timeout=60.0)
            
            if response.status_code != 200:
                return None

            # Use PyPDF2 or pdfplumber for extraction
            import io
            try:
                import pdfplumber
                pdf_file = io.BytesIO(response.content)
                text_parts = []
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                return "\n".join(text_parts)
            except ImportError:
                # Fallback to PyPDF2
                try:
                    import PyPDF2
                    pdf_file = io.BytesIO(response.content)
                    reader = PyPDF2.PdfReader(pdf_file)
                    text_parts = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    return "\n".join(text_parts)
                except ImportError:
                    return None

        except Exception:
            return None

    def _extract_financials_from_text(self, text: str, company_name: str) -> Dict[str, Any]:
        """Extract structured financial data from DRHP/RHP text."""
        statements = []
        
        # Look for financial statement sections
        # Common patterns in Indian DRHP/RHP
        import re
        
        # Pattern for revenue/profit tables
        # This is a simplified extraction - real implementation would be more sophisticated
        
        # Look for "Restated Standalone Financial Information" or similar sections
        financial_section = self._find_financial_section(text)
        
        if not financial_section:
            return {"statements": []}

        # Extract tables from financial section
        # Pattern for FY2024, FY2023, etc. with revenue, PAT, etc.
        year_pattern = r'(FY\s*20\d{2}|20\d{2}\s*[-–]\s*20\d{2})'
        years = re.findall(year_pattern, financial_section, re.IGNORECASE)
        
        # Extract revenue, PAT, EBITDA for each year
        for year in years[:8]:  # Max 8 periods
            # Search around each year for financial metrics
            year_idx = financial_section.lower().find(year.lower())
            if year_idx >= 0:
                context = financial_section[max(0, year_idx-500):year_idx+500]
                
                stmt = {
                    "period_end": year,
                    "period_type": "annual",
                    "revenue": self._extract_metric(context, ["revenue", "total income", "income from operations"]),
                    "net_income": self._extract_metric(context, ["profit after tax", "pat", "net profit"]),
                    "ebitda": self._extract_metric(context, ["ebitda", "operating profit"]),
                    "total_assets": self._extract_metric(context, ["total assets"]),
                    "total_equity": self._extract_metric(context, ["total equity", "net worth", "shareholders' funds"]),
                    "total_debt": self._extract_metric(context, ["total debt", "borrowings"]),
                    "cash_and_equivalents": self._extract_metric(context, ["cash and cash equivalents", "cash & bank balances"]),
                }
                statements.append(stmt)

        return {"statements": statements}

    def _find_financial_section(self, text: str) -> Optional[str]:
        """Find the financial statements section in DRHP/RHP."""
        markers = [
            "restated standalone financial information",
            "restated consolidated financial information", 
            "financial statements",
            "statement of profit and loss",
            "balance sheet",
            "restated summary statement of profits and losses",
            "restated summary statement of assets and liabilities",
        ]
        
        text_lower = text.lower()
        for marker in markers:
            idx = text_lower.find(marker)
            if idx >= 0:
                # Return section from marker onwards (up to ~50k chars)
                return text[idx:idx+50000]
        
        return None

    def _extract_metric(self, context: str, keywords: List[str]) -> Optional[float]:
        """Extract a financial metric value from context."""
        import re
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            idx = context.lower().find(keyword_lower)
            if idx >= 0:
                # Look for numbers near the keyword
                search_area = context[max(0, idx-100):idx+200]
                # Pattern for Indian number format: 1,234.56 or 1,23,45.67 (crore/lakh)
                numbers = re.findall(r'[\d,]+\.?\d*\s*(?:crore|cr|lakh|l)?', search_area, re.IGNORECASE)
                for num_str in numbers:
                    val = self._parse_indian_number(num_str)
                    if val is not None and val > 0:
                        return val
        return None

    def _parse_indian_number(self, num_str: str) -> Optional[float]:
        """Parse Indian number format (crore, lakh)."""
        num_str = num_str.strip().lower()
        
        multiplier = 1
        if 'crore' in num_str or num_str.endswith(' cr'):
            multiplier = 10000000  # 1 crore = 10 million
        elif 'lakh' in num_str or num_str.endswith(' l'):
            multiplier = 100000   # 1 lakh = 100 thousand
        
        # Extract numeric part
        import re
        match = re.search(r'[\d,]+\.?\d*', num_str)
        if match:
            try:
                return float(match.group().replace(',', '')) * multiplier
            except ValueError:
                pass
        return None

    def _safe_float(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None