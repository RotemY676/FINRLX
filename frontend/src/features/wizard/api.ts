/**
 * Phase W-3 — investor-profile wizard API helpers.
 *
 * Bearer-authenticated wrappers for the W-2 endpoints. Mirrors the
 * pattern used by saved-views (api.ts §B3).
 */
import { getAccessToken } from "@/services/auth";

import type { AnswerMap, InvestorProfile, ProfileMeResponse, ProfileStep } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

interface ApiEnvelope<T> {
  meta: unknown;
  data: T;
}

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const t = getAccessToken();
  const headers: Record<string, string> = { ...extra };
  if (t) headers.Authorization = `Bearer ${t}`;
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...authHeaders(),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Profile API ${res.status}: ${body || res.statusText}`);
  }
  const envelope = (await res.json()) as ApiEnvelope<T>;
  return envelope.data;
}

export async function fetchProfileQuestions(): Promise<ProfileStep[]> {
  return request<ProfileStep[]>("/api/v1/profile/questions");
}

export async function fetchMyProfile(): Promise<ProfileMeResponse> {
  return request<ProfileMeResponse>("/api/v1/profile/me");
}

export async function submitProfile(
  answers: AnswerMap,
  changeSummary?: string,
): Promise<InvestorProfile> {
  return request<InvestorProfile>("/api/v1/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers, change_summary: changeSummary }),
  });
}
