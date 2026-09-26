/**
 * Domain types for AI Creator Collaboration Workbench Demo.
 * Mock data is marked with data_origin; real model output is never pre-seeded in JSON.
 */

export type DataOrigin = "mock_seed" | "mock_api_response" | "real_model_output";

export type Platform = "tiktok" | "instagram";

export type ProductRelation =
  | "own_brand_user"
  | "own_brand_cooperation"
  | "competitor_user"
  | "competitor_cooperation_active"
  | "competitor_cooperation_ended"
  | "similar_product_user"
  | "category_mentions_only"
  | "unknown";

export type ExclusivityRisk = "none" | "possible" | "confirmed";

export type DataQualityLevel = "known" | "partial" | "unknown";

export type DecisionHint =
  | "recommend"
  | "recommend_after_relax"
  | "reject"
  | "review"
  | "exclude";

export type ScenarioTag =
  | "strong_candidate"
  | "strong_candidate_round2"
  | "cross_platform"
  | "gpm_known"
  | "gpm_unknown"
  | "gpm_diff_cross_platform"
  | "similar_product_user"
  | "own_brand_user"
  | "own_brand_cooperated"
  | "keyword_mismatch"
  | "audience_unknown"
  | "new_creator"
  | "coop_efficiency_known"
  | "competitor_exclusivity_unknown"
  | "competitor_active"
  | "competitor_ended"
  | "competitor_negative_review"
  | "competitor_positive_review"
  | "multi_product_neutral"
  | "first_round_pass"
  | "second_round_pass";

export interface MockMeta {
  is_mock: true;
  data_origin: "mock_seed";
  platform: Platform;
  schema_version: string;
  seed: number;
  generated_at: string;
  mock_disclaimer: string;
}

export interface BrandConfig {
  brand_id: string;
  name: string;
  product: string;
  category: string;
  target_audience: string[];
  platform_preference: Platform[];
  key_features: string[];
  tone: string;
  exclusion_rules: string[];
  target_gpm: number;
  data_origin: "mock_seed";
}

export interface ParsedGoal {
  brand: string;
  target_audience: string[];
  platform_preference: Platform[];
  target_count: number;
  inclusion_criteria: string[];
  exclusion_criteria: string[];
  outreach_count: number;
  needs_user_approval: true;
  target_gpm: number;
}

export interface ScenarioConfig {
  original_query: string;
  parsed_goal: ParsedGoal;
}

export interface AudienceInfo {
  status: "known" | "unknown";
  age_range: string | null;
  gender: string | null;
  regions: string[] | null;
  interests: string[] | null;
  note: string | null;
}

export interface ProductUsageEvidence {
  evidence_id: string;
  evidence_type: "organic_post" | "sponsored_post" | "bio_mention" | "comment";
  product_name: string;
  product_relation: ProductRelation;
  evidence_text: string;
  source_post_id: string;
  confidence: number;
  data_origin: "mock_seed";
}

export interface CooperationPerformance {
  play_count: number | null;
  engagement_rate: number | null;
  gmv: number | null;
  impressions: number | null;
  video_gpm?: number | null;
  gpm?: number | null;
}

export interface CooperationRecord {
  cooperation_id: string;
  brand_name: string;
  product: string;
  platform: Platform;
  is_current_brand: boolean;
  product_relation: ProductRelation;
  exclusivity_risk: ExclusivityRisk;
  sample_sent_at: string | null;
  sample_received_at: string | null;
  content_published_at: string | null;
  turnaround_days: number | null;
  deliverable: string | null;
  on_time: boolean | null;
  revision_count: number | null;
  communication_score: number | null;
  performance: CooperationPerformance;
  notes: string | null;
  data_origin: "mock_seed";
}

export interface ContactInfo {
  preferred_channel: "tiktok_dm" | "instagram_dm" | "email" | "unknown";
  dm_available: boolean;
  email: string | null;
  consent_status: "granted" | "denied" | "unknown";
}

export interface DataQuality {
  audience: DataQualityLevel;
  metrics: DataQualityLevel;
  gpm: DataQualityLevel;
}

export interface ExpectedAiSignals {
  expected_decision_hint: DecisionHint;
  expected_reason: string;
}

/**
 * Runtime-only shape for real model output. Never pre-seeded in mock JSON.
 */
export interface RealModelOutputMarker {
  data_origin: "real_model_output";
  model_name: string;
  generated_at: string;
}

export interface ApiResponseEnvelope {
  status: "success" | "error";
  status_code: number;
  request_id: string;
  latency_ms: number;
  origin: "mock_api_response";
  limitations: string[];
  error_message?: string;
}

export interface SearchSnapshot {
  snapshot_id: string;
  platform: Platform;
  keyword: string;
  hashtags: string[];
  region: string;
  date_range: { start: string; end: string };
  total_results: number;
  returned_creator_ids: string[];
  api_response: ApiResponseEnvelope;
  status?: "success" | "error";
  status_code?: number;
  request_id?: string;
  data_origin: "mock_api_response";
  limitations?: string[];
}

export interface AccountConnectionSnapshot {
  snapshot_id: string;
  platform: Platform;
  creator_id: string | null;
  unique_id?: string | null;
  username?: string | null;
  connected: boolean;
  api_response: ApiResponseEnvelope;
  status?: "success" | "error";
  status_code?: number;
  request_id?: string;
  data_origin: "mock_api_response";
  limitations?: string[];
}

export interface CreatorBase {
  creator_id: string;
  display_name: string;
  is_new_creator: boolean;
  platform: Platform;
  handle: string;
  content_topics: string[];
  audience: AudienceInfo;
  product_usage_evidence: ProductUsageEvidence[];
  cooperation_history: CooperationRecord[];
  contact: ContactInfo;
  data_quality: DataQuality;
  scenario_tags: ScenarioTag[];
  expected_ai_signals: ExpectedAiSignals;
  raw_api_snapshot_ref: string | null;
  data_origin: "mock_seed";
}
