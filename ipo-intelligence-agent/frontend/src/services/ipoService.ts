import api from "./api";
import type { IPOResponse, CompanyProfileResponse, FinancialHistoryResponse } from "../types/ipo";

export interface IPOsListParams {
  limit?: number;
  offset?: number;
  status?: string;
  exchange?: string;
  sector?: string;
  from_date?: string;
  to_date?: string;
  region?: "india" | "foreign";
  phase?: "upcoming" | "current" | "listed";
}

export interface IPOsSearchParams {
  q: string;
  limit?: number;
}

export interface IPOsRecentParams {
  days?: number;
  limit?: number;
}

export const ipoService = {
  async listUpcoming(params?: IPOsListParams): Promise<IPOResponse[]> {
    const { data } = await api.get<IPOResponse[]>("/ipos/upcoming", { params });
    return data;
  },

  async getRecent(params?: IPOsRecentParams): Promise<IPOResponse[]> {
    const { data } = await api.get<IPOResponse[]>("/ipos/recent", { params });
    return data;
  },

  async search(params: IPOsSearchParams): Promise<IPOResponse[]> {
    const { data } = await api.get<IPOResponse[]>("/ipos/search", { params });
    return data;
  },

  async getBySymbol(symbol: string): Promise<IPOResponse> {
    const { data } = await api.get<IPOResponse>(`/ipos/${symbol}`);
    return data;
  },

  async getFinancials(symbol: string): Promise<FinancialHistoryResponse> {
    const { data } = await api.get<FinancialHistoryResponse>(
      `/ipos/financials/${symbol}`
    );
    return data;
  },

  async discover(params?: {
    lookahead_days?: number;
    sources?: string[];
    min_market_cap?: number;
  }): Promise<IPOResponse[]> {
    const { data } = await api.post<IPOResponse[]>("/ipos/discover", null, {
      params,
    });
    return data;
  },

  async getCompanyProfile(symbol: string): Promise<CompanyProfileResponse> {
    const { data } = await api.get<CompanyProfileResponse>(
      `/ipos/companies/${symbol}`
    );
    return data;
  },
};
