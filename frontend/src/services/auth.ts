/**
 * Auth service (Phase MVP-4).
 *
 * Wraps /api/v1/auth/{signup,login,refresh,logout,me}. Manages token
 * storage in localStorage. Provides getAccessToken() for use by the
 * apiFetch wrapper (Bearer injection).
 *
 * Note on storage: localStorage is XSS-readable. Acceptable for a closed
 * 5-15 peer beta; MVP-5 migrates to HttpOnly cookies.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

const ACCESS_KEY = "finrlx_access_token";
const REFRESH_KEY = "finrlx_refresh_token";

export interface AuthUser {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_token_expires_at: string;
}

export interface AuthResponse {
  user: AuthUser;
  tokens: TokenPair;
}

function url(path: string): string {
  const base = API_BASE_URL.replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, token);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setRefreshToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(REFRESH_KEY, token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function postJson<T>(
  path: string,
  body: Record<string, unknown>,
  withAuth = false,
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (withAuth) {
    const t = getAccessToken();
    if (t) headers.Authorization = `Bearer ${t}`;
  }
  const res = await fetch(url(path), {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

async function getJson<T>(path: string, withAuth = false): Promise<T> {
  const headers: Record<string, string> = {};
  if (withAuth) {
    const t = getAccessToken();
    if (t) headers.Authorization = `Bearer ${t}`;
  }
  const res = await fetch(url(path), { headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function signup(email: string, password: string): Promise<AuthResponse> {
  return postJson<AuthResponse>("/api/v1/auth/signup", { email, password });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return postJson<AuthResponse>("/api/v1/auth/login", { email, password });
}

export function refreshTokens(refreshToken: string): Promise<TokenPair> {
  return postJson<TokenPair>("/api/v1/auth/refresh", { refresh_token: refreshToken });
}

export function logout(refreshToken: string): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>(
    "/api/v1/auth/logout",
    { refresh_token: refreshToken },
    true,
  );
}

export function getMe(): Promise<AuthUser> {
  return getJson<AuthUser>("/api/v1/auth/me", true);
}
