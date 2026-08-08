import api from "./api";
import type {
  AnalysisResponse,
  JobResponse,
  JobStatsResponse,
} from "../types/analysis";

export const analysisService = {
  async analyze(symbol: string): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>("/analysis/analyze", {
      symbol,
    });
    return data;
  },

  async getResult(symbol: string): Promise<AnalysisResponse> {
    const { data } = await api.get<AnalysisResponse>(
      `/analysis/results/${symbol}`
    );
    return data;
  },

  async getHistory(symbol: string): Promise<AnalysisResponse[]> {
    const { data } = await api.get<AnalysisResponse[]>(
      `/analysis/history/${symbol}`
    );
    return data;
  },

  async getJobStats(): Promise<JobStatsResponse> {
    const { data } = await api.get<JobStatsResponse>("/analysis/jobs/stats");
    return data;
  },

  async getPendingJobs(params?: {
    job_type?: string;
    limit?: number;
  }): Promise<JobResponse[]> {
    const { data } = await api.get<JobResponse[]>("/analysis/jobs", {
      params,
    });
    return data;
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const { data } = await api.get<JobResponse>(`/analysis/jobs/${jobId}`);
    return data;
  },

  async generateReport(symbol: string): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>("/analysis/report", {
      symbol,
    });
    return data;
  },

  async getReport(symbol: string): Promise<AnalysisResponse> {
    const { data } = await api.get<AnalysisResponse>(
      `/analysis/report/${symbol}`
    );
    return data;
  },

  async listReports(limit = 50): Promise<AnalysisResponse[]> {
    const { data } = await api.get<AnalysisResponse[]>("/analysis/reports", {
      params: { limit },
    });
    return data;
  },

  async collectData(symbol: string): Promise<{ job_id: string }> {
    const { data } = await api.post<{ job_id: string }>(
      "/analysis/collect",
      { symbol }
    );
    return data;
  },

  async runReflection(params?: {
    min_delay_days?: number;
    batch_size?: number;
  }): Promise<{ job_id: string }> {
    const { data } = await api.post<{ job_id: string }>(
      "/analysis/reflection",
      params
    );
    return data;
  },

  async verifyOutcome(prediction_id: string): Promise<{ job_id: string }> {
    const { data } = await api.post<{ job_id: string }>(
      "/analysis/verify-outcome",
      { prediction_id }
    );
    return data;
  },
};
