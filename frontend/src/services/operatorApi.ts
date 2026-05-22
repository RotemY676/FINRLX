import { apiFetch, type ApiResponse } from "./api";
import { getAccessToken } from "./auth";

export type OperatorAnalysisSource = "gpt" | "claude" | "other";
export type OperatorAnalysisSurface = "decision" | "replay" | "news" | "manual";

export interface OperatorAnalysis {
  id: string;
  user_email: string;
  surface: OperatorAnalysisSurface;
  recommendation_id: string | null;
  source: OperatorAnalysisSource;
  prompt: string | null;
  response: string;
  note: string | null;
  created_at: string;
}

export interface CreateOperatorAnalysisPayload {
  surface: OperatorAnalysisSurface;
  recommendation_id?: string | null;
  source: OperatorAnalysisSource;
  prompt?: string | null;
  response: string;
  note?: string | null;
}

function authHeaders(): Record<string, string> {
  const t = getAccessToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function createOperatorAnalysis(
  payload: CreateOperatorAnalysisPayload,
): Promise<ApiResponse<OperatorAnalysis>> {
  return apiFetch<OperatorAnalysis>("/api/v1/operator/analyses", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
}

export async function listOperatorAnalyses(opts?: {
  recommendation_id?: string;
  surface?: OperatorAnalysisSurface;
  limit?: number;
}): Promise<ApiResponse<OperatorAnalysis[]>> {
  const qs = new URLSearchParams();
  if (opts?.recommendation_id) qs.set("recommendation_id", opts.recommendation_id);
  if (opts?.surface) qs.set("surface", opts.surface);
  if (opts?.limit) qs.set("limit", String(opts.limit));
  const q = qs.toString();
  return apiFetch<OperatorAnalysis[]>(
    `/api/v1/operator/analyses${q ? `?${q}` : ""}`,
    { headers: authHeaders() },
  );
}

export async function deleteOperatorAnalysis(
  id: string,
): Promise<ApiResponse<{ deleted: string }>> {
  return apiFetch<{ deleted: string }>(`/api/v1/operator/analyses/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}
