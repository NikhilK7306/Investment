export interface IPOResponse {
  symbol: string
  company_name: string
  exchange: string
  sector: string
  industry: string
  status: string
  expected_date: string | null
  price_range: { low: number; high: number } | null
  shares_offered: number | null
  valuation: { enterprise_value: number; equity_value: number } | null
  underwriters: string[]
  lead_underwriter: string
}

export interface FinancialPeriod {
  period: string
  period_end: string | null
  revenue: number | null
  revenue_growth_yoy: number | null
  gross_profit: number | null
  gross_margin: number | null
  operating_income: number | null
  operating_margin: number | null
  net_income: number | null
  net_margin: number | null
  ebitda: number | null
  free_cash_flow: number | null
  cash_and_equivalents: number | null
  total_debt: number | null
  total_equity: number | null
  debt_to_equity: number | null
  current_ratio: number | null
  roe: number | null
  roic: number | null
}

export interface FinancialHistoryResponse {
  symbol: string
  periods: FinancialPeriod[]
}

export interface CompanyProfileResponse {
  legal_name: string
  common_name: string
  description: string
  business_model: string
  sector: string
  industry: string
  headquarters: string
  founded_year: number | null
  employee_count: number | null
  website: string
  ceo: string
  cfo: string
  chairman: string
  board_members: string[]
  major_shareholders: Record<string, unknown>
  competitors: string[]
  competitive_advantages: string[]
  risk_factors: string[]
  key_products: string[]
  target_markets: string[]
  regulatory_environment: string
  esg_score: number | null
}
