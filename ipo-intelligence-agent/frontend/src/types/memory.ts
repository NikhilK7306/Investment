export interface MemoryEntry {
  id: string
  memory_type: string
  content: Record<string, unknown>
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
  access_count: number
  last_accessed: string | null
  ttl_days: number | null
}

export interface FailureResponse {
  failure_id: string
  agent_name: string
  error_type: string
  error_message: string
  root_cause: string
  attempted_fix: string
  resolved: boolean
  resolution: string
  category: string
  severity: string
  occurrences: number
  last_occurrence: string
  ipo_symbol: string | null
}

export interface SuccessResponse {
  success_id: string
  agent_name: string
  strategy_description: string
  prompt_used: string
  tool_sequence: string[]
  api_sequence: string[]
  confidence: number
  success_rate: number
  context: Record<string, unknown>
  ipo_symbol: string | null
  usage_count: number
  reuse_count: number
}

export interface KnowledgeResponse {
  concept: string
  description: string
  evidence: Record<string, unknown>[]
  confidence: number
  domain: string
  tags: string[]
  version: number
}

export interface BestPracticeResponse {
  practice_id: string
  practice_name: string
  description: string
  applicable_context: Record<string, unknown>
  success_rate: number
  usage_count: number
  tags: string[]
  version: number
}

export interface ReflectionItem {
  prediction_id: string
  ipo_symbol: string
  prediction_type: string
  predicted_value: number
  actual_value: number
  accuracy: number
  error: number
  mistakes_identified: string[]
  correct_assumptions: string[]
  missing_factors: string[]
  lessons_extracted: string[]
  prompt_improvements: string[]
  strategy_changes: string[]
  knowledge_updates: string[]
  processed: boolean
  created_at: string
}

export interface LessonResponse {
  id: string
  lesson_type: string
  title: string
  description: string
  do: string[]
  dont: string[]
  best_practices: string[]
  anti_patterns: string[]
  known_bugs: string[]
  prompt_improvements: string[]
  confidence: number
  evidence: Record<string, unknown>[]
  applicable_agents: string[]
  tags: string[]
  version: number
  created_at: string
  updated_at: string
}
