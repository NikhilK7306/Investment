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
  agent_results: Record<string, unknown>
  completed_at: string | null
  error: string | null
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
