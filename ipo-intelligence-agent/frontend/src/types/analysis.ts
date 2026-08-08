export interface AnalysisResponse {
  job_id: string
  symbol: string
  status: string
  overall_score: number | null
  confidence: number | null
  recommendation: string | null
  risk_level: string | null
  time_horizon: string | null
  bull_case: string | null
  bear_case: string | null
  key_risks: string[]
  key_catalysts: string[]
  score_breakdown: Record<string, number>
  agent_results: Record<string, unknown>
  completed_at: string | null
  error: string | null
}

export interface ReportData {
  id: string
  ipo_id: string
  analysis_id: string
  title: string
  executive_summary: string
  ipo_overview: string
  company_background: string
  industry_analysis: string
  financial_analysis: string
  valuation_analysis: string
  risk_analysis: string
  management_assessment: string
  sentiment_analysis: string
  bull_case: string
  bear_case: string
  investment_thesis: string
  recommendation: string
  key_metrics: Record<string, number | string>
  financial_tables: Record<string, unknown>[]
  charts: Record<string, unknown>[]
  sources: Record<string, string>[]
  disclaimers: string[]
  format: string
  version: string
  generated_by: string
  model_version: string
  created_at: string
  updated_at: string
}

export interface JobResponse {
  id: string
  job_type: string
  status: string
  priority: number
  payload: Record<string, unknown>
  result: Record<string, unknown> | null
  error: string | null
  retry_count: number
  scheduled_at: string | null
  started_at: string | null
  completed_at: string | null
  worker_id: string | null
}

export interface JobStatsResponse {
  by_type: Record<string, Record<string, number>>
  total_pending: number
  total_running: number
  total_completed: number
  total_failed: number
}
