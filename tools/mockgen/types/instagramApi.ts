/**
 * Instagram Graph API-aligned attribute types for mock creator data.
 * Field names mirror Instagram Graph API User / Media objects.
 */

import type {
  AccountConnectionSnapshot,
  BrandConfig,
  CreatorBase,
  MockMeta,
  ScenarioConfig,
  SearchSnapshot,
} from "./domain";

/** Instagram Profile attributes (Graph API User fields). */
export interface InstagramProfileAttributes {
  ig_id: string;
  username: string;
  name: string;
  biography: string;
  followers_count: number;
  follows_count: number;
  media_count: number;
  website: string | null;
  profile_picture_url: string;
}

export type InstagramMediaType = "IMAGE" | "VIDEO" | "CAROUSEL_ALBUM" | "REELS";

/** Instagram Media attributes (Graph API Media fields). */
export interface InstagramMediaAttributes {
  id: string;
  media_url: string;
  caption: string;
  permalink: string;
  media_type: InstagramMediaType;
  like_count: number;
  comments_count: number;
  timestamp: string;
}

/**
 * Instagram commerce / GPM extension.
 * Native Graph API has no GPM; these are Demo extension fields.
 */
export interface InstagramMetrics {
  avg_play_count_30d: number | null;
  engagement_rate_30d: number | null;
  growth_rate_30d: number | null;
  gmv_30d: number | null;
  impressions_30d: number | null;
  /** GPM = gmv_30d / impressions_30d * 1000 (extension field) */
  gpm_30d: number | null;
  currency: "USD" | "CNY" | "unknown";
  units_sold_30d: number | null;
  gmv_per_buyer: number | null;
  gpm_origin: "mock_seed" | "unknown";
}

export interface InstagramCreator extends CreatorBase {
  platform: "instagram";
  profile: InstagramProfileAttributes;
  metrics: InstagramMetrics;
  recent_posts: InstagramMediaAttributes[];
}

export interface InstagramCreatorsFile {
  meta: MockMeta & { platform: "instagram" };
  brand: BrandConfig;
  scenario: ScenarioConfig;
  search_snapshots: SearchSnapshot[];
  account_connection_snapshots: AccountConnectionSnapshot[];
  creators: InstagramCreator[];
}
