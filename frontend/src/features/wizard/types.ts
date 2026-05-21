/**
 * Phase W-3 — investor-profile wizard TypeScript contract.
 *
 * Mirrors backend Pydantic schemas in app/schemas/profile.py exactly.
 */

export interface ProfileQuestionChoice {
  value: string;
  label: string;
  score: number | null;
}

export interface ProfileQuestion {
  code: string;
  step: number;
  order_in_step: number;
  dimension: string;
  text: string;
  helper_text: string | null;
  choices: ProfileQuestionChoice[];
  is_required: boolean;
  is_active: boolean;
}

export interface ProfileStep {
  step: number;
  label: string;
  dimension_hint: string;
  questions: ProfileQuestion[];
}

export interface InvestorProfile {
  id: string;
  user_id: string;
  version: number;
  risk_score: number;
  risk_bucket: string;
  horizon_band: string;
  primary_goal: string;
  max_drawdown_pct: number;
  knowledge_level: string;
  years_investing: number;
  instruments_traded: string[];
  investable_amount_band: string;
  income_band: string;
  liquid_net_worth_band: string;
  sector_whitelist: string[];
  sector_blacklist: string[];
  region_preference: string;
  exclude_leverage: boolean;
  base_currency: string;
  trading_frequency: string;
  completed_at: string;
  created_at: string;
  updated_at: string;
  raw_answers?: AnswerMap | null;
}

export interface ProfileMeResponse {
  has_profile: boolean;
  profile: InvestorProfile | null;
}

/**
 * Single-value answers store as string; multi-select questions store
 * as string[] (e.g. K_03_INSTRUMENTS, U_02_SECTOR_WHITELIST,
 * U_03_SECTOR_BLACKLIST).
 */
export type AnswerValue = string | string[];
export type AnswerMap = Record<string, AnswerValue>;

export const MULTI_SELECT_CODES = new Set([
  "K_03_INSTRUMENTS",
  "U_02_SECTOR_WHITELIST",
  "U_03_SECTOR_BLACKLIST",
]);

export const TOTAL_STEPS = 8;
