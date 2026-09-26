/**
 * TikTok API-aligned attribute types for mock creator data.
 * Field names mirror common TikTok Open API / Research API user & video attributes.
 */

import type {
  AccountConnectionSnapshot,
  BrandConfig,
  CreatorBase,
  MockMeta,
  ScenarioConfig,
  SearchSnapshot,
} from "./domain";

/** TikTok User attributes (aligned with TikTok API user object fields). */
export interface TikTokUserAttributes {
  uid: string;
  unique_id: string;
  nickname: string;
  sec_uid: string;
  signature: string;
  follower_count: number;
  following_count: number;
  heart_count: number;
  video_count: number;
  verified: boolean;
  region: string;
  bio_url: string | null;
  category: string | null;
  avatar_thumb: string;
}

export interface TikTokMusicInfo {
  music_id: string;
  music_name: string;
  author_name: string;
}

export interface TikTokVideoStats {
  play_count: number;
  digg_count: number;
  comment_count: number;
  share_count: number;
  collect_count: number;
}

/** TikTok Video attributes. */
export interface TikTokVideoAttributes {
  video_id: string;
  share_url: string;
  create_time: number;
  title: string;
  duration: number;
  cover_urls: string[];
  region: string;
  hashtag_names: string[];
  music_info: TikTokMusicInfo;
  stats: TikTokVideoStats;
}

/** TikTok commerce / GPM metrics (Shop / affiliate style). */
export interface TikTokMetrics {
  avg_play_count_30d: number | null;
  engagement_rate_30d: number | null;
  growth_rate_30d: number | null;
  gmv_30d: number | null;
  impressions_30d: number | null;
  /** GPM = gmv_30d / impressions_30d * 1000 */
  video_gpm: number | null;
  currency: "USD" | "CNY" | "unknown";
  units_sold_30d: number | null;
  gmv_per_buyer: number | null;
  gpm_origin: "mock_seed" | "unknown";
}

export interface TikTokCreator extends CreatorBase {
  platform: "tiktok";
  profile: TikTokUserAttributes;
  metrics: TikTokMetrics;
  recent_posts: TikTokVideoAttributes[];
}

export interface TikTokCreatorsFile {
  meta: MockMeta & { platform: "tiktok" };
  brand: BrandConfig;
  scenario: ScenarioConfig;
  search_snapshots: SearchSnapshot[];
  account_connection_snapshots: AccountConnectionSnapshot[];
  creators: TikTokCreator[];
}
