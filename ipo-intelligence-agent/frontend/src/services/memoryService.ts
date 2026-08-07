import api from "./api";
import type {
  MemoryEntry,
  FailureResponse,
  SuccessResponse,
  KnowledgeResponse,
  BestPracticeResponse,
  ReflectionItem,
  LessonResponse,
} from "../types/memory";

export const memoryService = {
  async getRecent(params?: {
    memory_type?: string;
    limit?: number;
  }): Promise<MemoryEntry[]> {
    const { data } = await api.get<MemoryEntry[]>("/memory/recent", {
      params,
    });
    return data;
  },

  async getFailures(params?: {
    resolved?: boolean;
    category?: string;
    limit?: number;
  }): Promise<FailureResponse[]> {
    const { data } = await api.get<FailureResponse[]>("/memory/failures", {
      params,
    });
    return data;
  },

  async getUnresolvedFailures(): Promise<FailureResponse[]> {
    const { data } = await api.get<FailureResponse[]>(
      "/memory/failures/unresolved"
    );
    return data;
  },

  async resolveFailure(failureId: string): Promise<{ resolved: boolean }> {
    const { data } = await api.post<{ resolved: boolean }>(
      `/memory/failures/${failureId}/resolve`
    );
    return data;
  },

  async getSuccesses(params?: {
    limit?: number;
  }): Promise<SuccessResponse[]> {
    const { data } = await api.get<SuccessResponse[]>("/memory/successes", {
      params,
    });
    return data;
  },

  async getKnowledge(params?: {
    domain?: string;
    limit?: number;
  }): Promise<KnowledgeResponse[]> {
    const { data } = await api.get<KnowledgeResponse[]>("/memory/knowledge", {
      params,
    });
    return data;
  },

  async getKnowledgeByConcept(concept: string): Promise<KnowledgeResponse> {
    const { data } = await api.get<KnowledgeResponse>(
      `/memory/knowledge/concept/${concept}`
    );
    return data;
  },

  async getBestPractices(params?: {
    applicable?: boolean;
    limit?: number;
  }): Promise<BestPracticeResponse[]> {
    const { data } = await api.get<BestPracticeResponse[]>(
      "/memory/best-practices",
      { params }
    );
    return data;
  },

  async getReflections(params?: {
    processed?: boolean;
    limit?: number;
  }): Promise<ReflectionItem[]> {
    const { data } = await api.get<ReflectionItem[]>(
      "/memory/reflections",
      { params }
    );
    return data;
  },

  async getReflectionsByIpo(symbol: string): Promise<ReflectionItem[]> {
    const { data } = await api.get<ReflectionItem[]>(
      `/memory/reflections/ipo/${symbol}`
    );
    return data;
  },

  async getUnprocessedReflections(): Promise<ReflectionItem[]> {
    const { data } = await api.get<ReflectionItem[]>(
      "/memory/reflections/unprocessed"
    );
    return data;
  },

  async getLessons(params?: {
    lesson_type?: string;
    limit?: number;
  }): Promise<LessonResponse[]> {
    const { data } = await api.get<LessonResponse[]>("/memory/lessons", {
      params,
    });
    return data;
  },

  async getLessonById(lessonId: string): Promise<LessonResponse> {
    const { data } = await api.get<LessonResponse>(
      `/memory/lessons/${lessonId}`
    );
    return data;
  },

  async getLessonsByType(lessonType: string): Promise<LessonResponse[]> {
    const { data } = await api.get<LessonResponse[]>(
      `/memory/lessons/type/${lessonType}`
    );
    return data;
  },
};
