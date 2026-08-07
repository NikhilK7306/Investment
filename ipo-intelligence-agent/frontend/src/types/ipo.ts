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
