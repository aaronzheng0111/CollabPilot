/**
 * Deterministic mock data generator for CollabPilot Demo.
 * Seed: 20260926 — rerunning yields identical JSON.
 *
 * Usage: npm run generate:mock   (from tools/mockgen)
 */

import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const SEED = 20260926;
const GENERATED_AT = "2026-09-26T00:00:00Z";
const SCHEMA_VERSION = "1.0";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT_DIR = path.resolve(__dirname, "../../../data/mock");

/** Mulberry32 PRNG — deterministic given seed. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rng = mulberry32(SEED);

function pick<T>(arr: T[]): T {
  return arr[Math.floor(rng() * arr.length)]!;
}

function randInt(min: number, max: number): number {
  return Math.floor(rng() * (max - min + 1)) + min;
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function round3(n: number): number {
  return Math.round(n * 1000) / 1000;
}

function calcGpm(gmv: number, impressions: number): number {
  return round1((gmv / impressions) * 1000);
}

const MOCK_DISCLAIMER =
  "本文件所有达人、帖子、合作、GPM 均为模拟数据。真实模型输出由 Demo 运行时生成，标记为 real_model_output。";

const BRAND = {
  brand_id: "brand_linguago",
  name: "LinguaGo AI 翻译",
  product: "AI 翻译工具",
  category: "AI 效率工具",
  target_audience: ["中文用户", "留学生", "跨境从业者", "内容创作者", "职场人"],
  platform_preference: ["tiktok", "instagram"] as const,
  key_features: ["中英日韩互译", "文档翻译", "实时对话翻译", "术语库"],
  tone: "专业、直接、重视效率",
  exclusion_rules: [
    "已合作本品牌",
    "纯语言教学",
    "影视字幕剪辑",
    "翻译梗娱乐",
    "关键词命中但主题不匹配",
  ],
  target_gpm: 20,
  data_origin: "mock_seed" as const,
};

const SCENARIO = {
  original_query:
    "为一款面向中文用户的AI翻译工具，找10位使用这个翻译工具的创作者。优先选择最近持续发布相关内容的人，排除已经合作过的账号。整理候选名单，并为最合适的3位准备合作邀请草稿。发送前让我审核。",
  parsed_goal: {
    brand: "LinguaGo AI 翻译",
    target_audience: ["中文用户"],
    platform_preference: ["tiktok", "instagram"] as const,
    target_count: 10,
    inclusion_criteria: ["使用过该翻译工具", "最近持续发布相关内容"],
    exclusion_criteria: ["已经合作过的账号"],
    outreach_count: 3,
    needs_user_approval: true as const,
    target_gpm: 20,
  },
};

type Platform = "tiktok" | "instagram";
type ProductRelation =
  | "own_brand_user"
  | "own_brand_cooperation"
  | "competitor_user"
  | "competitor_cooperation_active"
  | "competitor_cooperation_ended"
  | "similar_product_user"
  | "category_mentions_only"
  | "unknown";

type Role =
  | "strong_r1"
  | "strong_r2"
  | "keyword_mismatch"
  | "own_brand_coop"
  | "audience_unknown"
  | "new_creator"
  | "competitor_active"
  | "competitor_ended"
  | "competitor_negative"
  | "competitor_positive"
  | "multi_neutral"
  | "similar_filler"
  | "gpm_unknown_filler";

interface CreatorDef {
  id: number;
  display_name: string;
  handle_base: string;
  platforms: Platform[];
  role: Role;
  topics: string[];
  product_relation: ProductRelation;
  /** Cross-platform GPM pair [tt, ig]; null = use defaults / unknown */
  gpm_pair?: { tt: number | null; ig: number | null };
  mismatch_note?: string;
}

/**
 * 34 unique creators.
 * Cross-platform: 001–010 (10)
 * TikTok-only: 011–022 (12)
 * Instagram-only: 023–034 (12)
 * Accounts: 44
 */
const CREATOR_DEFS: CreatorDef[] = [
  // —— Round-1 strong (6) ——
  {
    id: 1,
    display_name: "Amy学翻译",
    handle_base: "lingua.amy",
    platforms: ["tiktok", "instagram"],
    role: "strong_r1",
    topics: ["AI工具", "翻译", "跨境"],
    product_relation: "own_brand_user",
    gpm_pair: { tt: 14.4, ig: 30.0 }, // large cross-platform GPM diff
  },
  {
    id: 2,
    display_name: "跨境效率Ben",
    handle_base: "crossborder.ben",
    platforms: ["tiktok", "instagram"],
    role: "strong_r1",
    topics: ["跨境电商", "AI工具", "效率"],
    product_relation: "similar_product_user",
    gpm_pair: { tt: 18.2, ig: 22.5 },
  },
  {
    id: 3,
    display_name: "职场翻译Cora",
    handle_base: "work.cora",
    platforms: ["tiktok", "instagram"],
    role: "strong_r1",
    topics: ["职场", "文档翻译", "AI工具"],
    product_relation: "own_brand_user",
    gpm_pair: { tt: 21.0, ig: 19.5 },
  },
  {
    id: 4,
    display_name: "留学沟通Derek",
    handle_base: "study.derek",
    platforms: ["tiktok", "instagram"],
    role: "strong_r1",
    topics: ["留学", "实时对话", "翻译工具"],
    product_relation: "similar_product_user",
    gpm_pair: { tt: 16.8, ig: 17.2 },
  },
  {
    id: 5,
    display_name: "术语库Eva",
    handle_base: "termbase.eva",
    platforms: ["tiktok", "instagram"],
    role: "strong_r1",
    topics: ["术语库", "合同翻译", "效率"],
    product_relation: "competitor_cooperation_ended",
    gpm_pair: { tt: 24.0, ig: 26.1 },
  },
  {
    id: 6,
    display_name: "多产品测评Frank",
    handle_base: "tools.frank",
    platforms: ["tiktok", "instagram"],
    role: "strong_r1",
    topics: ["AI工具测评", "翻译", "效率对比"],
    product_relation: "similar_product_user",
    gpm_pair: { tt: 15.5, ig: 18.0 },
  },
  // —— Round-2 strong (3) → total 9 ——
  {
    id: 7,
    display_name: "新人Grace译",
    handle_base: "new.grace",
    platforms: ["tiktok", "instagram"],
    role: "strong_r2",
    topics: ["AI翻译", "留学生活", "效率"],
    product_relation: "own_brand_user",
    gpm_pair: { tt: 12.0, ig: 13.5 },
  },
  {
    id: 8,
    display_name: "跨境Hank",
    handle_base: "cb.hanks",
    platforms: ["tiktok", "instagram"],
    role: "strong_r2",
    topics: ["跨境", "中日韩互译", "办公"],
    product_relation: "similar_product_user",
    gpm_pair: { tt: 9.5, ig: 28.0 }, // large GPM diff
  },
  {
    id: 9,
    display_name: "效率Iris",
    handle_base: "eff.iris",
    platforms: ["tiktok", "instagram"],
    role: "strong_r2",
    topics: ["职场效率", "文档翻译", "AI"],
    product_relation: "own_brand_user",
    gpm_pair: { tt: 17.0, ig: 16.2 },
  },
  // —— Competitor active + exclusivity + GPM diff ——
  {
    id: 10,
    display_name: "竞品合作Jake",
    handle_base: "comp.jake",
    platforms: ["tiktok", "instagram"],
    role: "competitor_active",
    topics: ["AI翻译", "工具推荐"],
    product_relation: "competitor_cooperation_active",
    gpm_pair: { tt: 11.0, ig: 35.0 }, // large GPM diff
  },
  // —— Keyword mismatch (5) ——
  {
    id: 11,
    display_name: "翻译剪辑君",
    handle_base: "subtitle.cut",
    platforms: ["tiktok"],
    role: "keyword_mismatch",
    topics: ["影视字幕", "剪辑", "娱乐"],
    product_relation: "category_mentions_only",
    mismatch_note: "昵称含翻译，内容为影视字幕剪辑",
  },
  {
    id: 12,
    display_name: "英语考试通",
    handle_base: "exam.english",
    platforms: ["tiktok"],
    role: "keyword_mismatch",
    topics: ["雅思", "托福", "考试英语"],
    product_relation: "category_mentions_only",
    mismatch_note: "昵称含英语，内容为考试英语",
  },
  {
    id: 13,
    display_name: "AI绘画Mia",
    handle_base: "ai.paint.mia",
    platforms: ["tiktok"],
    role: "keyword_mismatch",
    topics: ["AI绘画", "Midjourney", "插画"],
    product_relation: "category_mentions_only",
    mismatch_note: "昵称含AI，内容为AI绘画",
  },
  {
    id: 14,
    display_name: "留学申请Nina",
    handle_base: "apply.nina",
    platforms: ["instagram"],
    role: "keyword_mismatch",
    topics: ["留学申请", "文书", "选校"],
    product_relation: "category_mentions_only",
    mismatch_note: "昵称含留学，内容为留学申请",
  },
  {
    id: 15,
    display_name: "小语种备考Owen",
    handle_base: "lang.exam.owen",
    platforms: ["instagram"],
    role: "keyword_mismatch",
    topics: ["日语N1", "韩语TOPIK", "语言考试"],
    product_relation: "category_mentions_only",
    mismatch_note: "昵称含小语种，内容为语言考试",
  },
  // —— Own brand cooperated (4) ——
  {
    id: 16,
    display_name: "已合作Paula",
    handle_base: "done.paula",
    platforms: ["tiktok"],
    role: "own_brand_coop",
    topics: ["AI翻译", "效率工具"],
    product_relation: "own_brand_cooperation",
  },
  {
    id: 17,
    display_name: "已合作Quinn",
    handle_base: "done.quinn",
    platforms: ["tiktok"],
    role: "own_brand_coop",
    topics: ["跨境", "翻译工具"],
    product_relation: "own_brand_cooperation",
  },
  {
    id: 18,
    display_name: "已合作Rita",
    handle_base: "done.rita",
    platforms: ["instagram"],
    role: "own_brand_coop",
    topics: ["职场", "文档翻译"],
    product_relation: "own_brand_cooperation",
  },
  {
    id: 19,
    display_name: "已合作Sam",
    handle_base: "done.sam",
    platforms: ["instagram"],
    role: "own_brand_coop",
    topics: ["留学生", "AI工具"],
    product_relation: "own_brand_cooperation",
  },
  // —— Audience unknown (4) ——
  {
    id: 20,
    display_name: "画像缺失Tina",
    handle_base: "unk.tina",
    platforms: ["tiktok"],
    role: "audience_unknown",
    topics: ["AI工具", "翻译"],
    product_relation: "similar_product_user",
    gpm_pair: { tt: null, ig: null },
  },
  {
    id: 21,
    display_name: "画像缺失Uma",
    handle_base: "unk.uma",
    platforms: ["tiktok"],
    role: "audience_unknown",
    topics: ["跨境", "效率"],
    product_relation: "own_brand_user",
    gpm_pair: { tt: null, ig: null },
  },
  {
    id: 22,
    display_name: "画像缺失Vince",
    handle_base: "unk.vince",
    platforms: ["instagram"],
    role: "audience_unknown",
    topics: ["职场", "翻译工具"],
    product_relation: "similar_product_user",
    gpm_pair: { tt: null, ig: null },
  },
  {
    id: 23,
    display_name: "画像缺失Wendy",
    handle_base: "unk.wendy",
    platforms: ["instagram"],
    role: "audience_unknown",
    topics: ["AI翻译", "留学生"],
    product_relation: "competitor_user",
    gpm_pair: { tt: null, ig: null },
  },
  // —— New creators (4) ——
  {
    id: 24,
    display_name: "新人Xander译",
    handle_base: "new.xander",
    platforms: ["tiktok"],
    role: "new_creator",
    topics: ["AI翻译", "实时对话"],
    product_relation: "own_brand_user",
  },
  {
    id: 25,
    display_name: "新人Yuna工具",
    handle_base: "new.yuna",
    platforms: ["tiktok"],
    role: "new_creator",
    topics: ["效率工具", "文档翻译"],
    product_relation: "similar_product_user",
  },
  {
    id: 26,
    display_name: "新人Zack跨境",
    handle_base: "new.zack",
    platforms: ["instagram"],
    role: "new_creator",
    topics: ["跨境沟通", "中英互译"],
    product_relation: "own_brand_user",
  },
  {
    id: 27,
    display_name: "新人Ava术语",
    handle_base: "new.ava.term",
    platforms: ["instagram"],
    role: "new_creator",
    topics: ["术语库", "合同"],
    product_relation: "similar_product_user",
  },
  // —— Extra competitor / review / neutral / fillers ——
  {
    id: 28,
    display_name: "深度竞品Blair",
    handle_base: "deep.blair",
    platforms: ["tiktok"],
    role: "competitor_active",
    topics: ["翻译App", "竞品评测"],
    product_relation: "competitor_cooperation_active",
  },
  {
    id: 29,
    display_name: "竞品已结束Chris",
    handle_base: "ended.chris",
    platforms: ["instagram"],
    role: "competitor_ended",
    topics: ["AI工具", "翻译对比"],
    product_relation: "competitor_cooperation_ended",
  },
  {
    id: 30,
    display_name: "竞品差评Dana",
    handle_base: "neg.dana",
    platforms: ["tiktok"],
    role: "competitor_negative",
    topics: ["翻译工具吐槽", "AI效率"],
    product_relation: "competitor_user",
  },
  {
    id: 31,
    display_name: "竞品好评Eli",
    handle_base: "pos.eli",
    platforms: ["instagram"],
    role: "competitor_positive",
    topics: ["DeepL粉", "翻译推荐"],
    product_relation: "competitor_user",
  },
  {
    id: 32,
    display_name: "中立测评Faye",
    handle_base: "neutral.faye",
    platforms: ["tiktok"],
    role: "multi_neutral",
    topics: ["多产品对比", "翻译工具", "效率"],
    product_relation: "similar_product_user",
  },
  {
    id: 33,
    display_name: "类品用户Gus",
    handle_base: "sim.gus",
    platforms: ["instagram"],
    role: "similar_filler",
    topics: ["笔记+翻译", "跨境办公"],
    product_relation: "similar_product_user",
  },
  {
    id: 34,
    display_name: "GPM缺失Holly",
    handle_base: "nogpm.holly",
    platforms: ["tiktok"],
    role: "gpm_unknown_filler",
    topics: ["AI翻译", "职场"],
    product_relation: "own_brand_user",
    gpm_pair: { tt: null, ig: null },
  },
];

function padId(n: number): string {
  return String(n).padStart(3, "0");
}

function creatorId(n: number): string {
  return `creator_${padId(n)}`;
}

function tagsFor(def: CreatorDef, platform: Platform): string[] {
  const tags = new Set<string>();
  if (def.platforms.length === 2) tags.add("cross_platform");

  switch (def.role) {
    case "strong_r1":
      tags.add("strong_candidate");
      tags.add("first_round_pass");
      tags.add("coop_efficiency_known");
      tags.add("gpm_known");
      if (def.id === 6) tags.add("multi_product_neutral");
      break;
    case "strong_r2":
      tags.add("strong_candidate_round2");
      tags.add("second_round_pass");
      if (def.id === 7) tags.add("new_creator");
      tags.add("gpm_known");
      break;
    case "keyword_mismatch":
      tags.add("keyword_mismatch");
      break;
    case "own_brand_coop":
      tags.add("own_brand_cooperated");
      tags.add("gpm_known");
      break;
    case "audience_unknown":
      tags.add("audience_unknown");
      tags.add("gpm_unknown");
      break;
    case "new_creator":
      tags.add("new_creator");
      tags.add("gpm_known");
      break;
    case "competitor_active":
      tags.add("competitor_active");
      tags.add("competitor_exclusivity_unknown");
      tags.add("gpm_known");
      break;
    case "competitor_ended":
      tags.add("competitor_ended");
      tags.add("gpm_known");
      break;
    case "competitor_negative":
      tags.add("competitor_negative_review");
      tags.add("gpm_known");
      break;
    case "competitor_positive":
      tags.add("competitor_positive_review");
      tags.add("gpm_known");
      break;
    case "multi_neutral":
      tags.add("multi_product_neutral");
      tags.add("gpm_known");
      break;
    case "similar_filler":
      tags.add("similar_product_user");
      tags.add("gpm_known");
      break;
    case "gpm_unknown_filler":
      tags.add("gpm_unknown");
      tags.add("own_brand_user");
      break;
  }

  if (
    def.product_relation === "similar_product_user" ||
    def.product_relation === "competitor_user"
  ) {
    tags.add("similar_product_user");
  }
  if (def.product_relation === "own_brand_user") tags.add("own_brand_user");

  if (
    def.gpm_pair &&
    def.platforms.length === 2 &&
    def.gpm_pair.tt != null &&
    def.gpm_pair.ig != null &&
    Math.abs(def.gpm_pair.tt - def.gpm_pair.ig) >= 10
  ) {
    tags.add("gpm_diff_cross_platform");
  }

  if (def.gpm_pair?.[platform === "tiktok" ? "tt" : "ig"] === null) {
    tags.add("gpm_unknown");
  }

  return [...tags];
}

function expectedSignals(def: CreatorDef): {
  expected_decision_hint: string;
  expected_reason: string;
} {
  switch (def.role) {
    case "strong_r1":
      return {
        expected_decision_hint: "recommend",
        expected_reason: "产品相关、近期持续发布、合作效率高、可进入首轮名单",
      };
    case "strong_r2":
      return {
        expected_decision_hint: "recommend_after_relax",
        expected_reason: "首轮偏严未入选；放宽时间/粉丝门槛后可进入二轮名单",
      };
    case "keyword_mismatch":
      return {
        expected_decision_hint: "reject",
        expected_reason:
          def.mismatch_note ?? "关键词命中，但内容主题与品牌目标不匹配",
      };
    case "own_brand_coop":
      return {
        expected_decision_hint: "exclude",
        expected_reason: "已合作本品牌，硬排除",
      };
    case "audience_unknown":
      return {
        expected_decision_hint: "review",
        expected_reason: "受众画像缺失，降权待确认，不编造受众",
      };
    case "new_creator":
      return {
        expected_decision_hint: "review",
        expected_reason: "新人无历史合作，按产品相关度与近30天流量排序",
      };
    case "competitor_active":
      return {
        expected_decision_hint: "review",
        expected_reason: "竞品深度合作中，排他风险未知，需人工确认",
      };
    case "competitor_ended":
      return {
        expected_decision_hint: "recommend",
        expected_reason: "竞品合作已结束，可尝试触达",
      };
    case "competitor_negative":
      return {
        expected_decision_hint: "recommend",
        expected_reason: "竞品差评者转化潜力高，但需验证真实性",
      };
    case "competitor_positive":
      return {
        expected_decision_hint: "review",
        expected_reason: "竞品好评者转化难度大，降权",
      };
    case "multi_neutral":
      return {
        expected_decision_hint: "recommend",
        expected_reason: "多产品中立测评型，适合对比测评合作",
      };
    case "similar_filler":
      return {
        expected_decision_hint: "review",
        expected_reason: "类似产品使用者，可作参考候选但需评估转化风险",
      };
    case "gpm_unknown_filler":
      return {
        expected_decision_hint: "review",
        expected_reason: "产品相关但 GPM 缺失，降权不排除",
      };
  }
}

function audienceFor(def: CreatorDef) {
  if (def.role === "audience_unknown") {
    return {
      status: "unknown" as const,
      age_range: null,
      gender: null,
      regions: null,
      interests: null,
      note: "平台未公开受众画像，数据缺失",
    };
  }
  return {
    status: "known" as const,
    age_range: pick(["18-24", "20-30", "25-34", "22-28"]),
    gender: pick(["female_55", "female_60", "male_45", "mixed_50"]),
    regions: pick([
      ["北美", "东南亚"],
      ["北美", "欧洲"],
      ["东南亚", "中国大陆"],
      ["北美", "澳洲"],
    ]),
    interests: def.topics.slice(0, 3),
    note: null,
  };
}

function metricsFor(
  def: CreatorDef,
  platform: Platform,
): {
  avg_play_count_30d: number | null;
  engagement_rate_30d: number | null;
  growth_rate_30d: number | null;
  gmv_30d: number | null;
  impressions_30d: number | null;
  video_gpm?: number | null;
  gpm_30d?: number | null;
  currency: "USD" | "CNY" | "unknown";
  units_sold_30d: number | null;
  gmv_per_buyer: number | null;
  gpm_origin: "mock_seed" | "unknown";
} {
  const key = platform === "tiktok" ? "tt" : "ig";
  const targetGpm = def.gpm_pair?.[key];

  const gpmMissing =
    targetGpm === null ||
    def.role === "audience_unknown" ||
    def.role === "gpm_unknown_filler";

  if (gpmMissing) {
    const base = {
      avg_play_count_30d: randInt(8000, 45000),
      engagement_rate_30d: round3(0.02 + rng() * 0.05),
      growth_rate_30d: round2(0.05 + rng() * 0.2),
      gmv_30d: null,
      impressions_30d: null,
      currency: "unknown" as const,
      units_sold_30d: null,
      gmv_per_buyer: null,
      gpm_origin: "unknown" as const,
    };
    if (platform === "tiktok") {
      return { ...base, video_gpm: null };
    }
    return { ...base, gpm_30d: null };
  }

  const gpm = targetGpm ?? round1(10 + rng() * 20);
  const impressions = randInt(200000, 900000);
  const gmv = round1((gpm * impressions) / 1000);
  const units = randInt(80, 600);
  const base = {
    avg_play_count_30d: randInt(15000, 120000),
    engagement_rate_30d: round3(0.035 + rng() * 0.06),
    growth_rate_30d: round2(0.08 + rng() * 0.35),
    gmv_30d: gmv,
    impressions_30d: impressions,
    currency: "USD" as const,
    units_sold_30d: units,
    gmv_per_buyer: round1(gmv / units),
    gpm_origin: "mock_seed" as const,
  };
  if (platform === "tiktok") {
    return { ...base, video_gpm: gpm };
  }
  return { ...base, gpm_30d: gpm };
}

function evidenceText(def: CreatorDef, platform: Platform): string {
  const texts: Record<Role, string[]> = {
    strong_r1: [
      "最近用LinguaGo翻译海外合同，术语库很省时间",
      "实测中英日韩互译，跨境沟通效率提升明显",
      "职场文档翻译用LinguaGo，比手动查词快很多",
    ],
    strong_r2: [
      "刚开始用LinguaGo做实时对话翻译，留学生活更顺",
      "对比几款翻译工具后，文档翻译我选了LinguaGo",
    ],
    keyword_mismatch: [
      def.mismatch_note ?? "内容与翻译工具无关",
      "本期字幕剪辑花絮",
      "雅思阅读技巧分享",
    ],
    own_brand_coop: ["LinguaGo 合作视频已发布，感谢品牌寄样"],
    audience_unknown: ["分享了一款AI翻译工具的使用体验"],
    new_creator: ["第一次测评LinguaGo实时对话翻译"],
    competitor_active: ["本月继续和 Mock竞品翻译 合作中"],
    competitor_ended: ["之前和竞品合作已结束，最近在试用其他翻译工具"],
    competitor_negative: ["某竞品翻译翻车了，术语错误太多"],
    competitor_positive: ["一直爱用某竞品翻译，体验很好"],
    multi_neutral: ["五款翻译工具横评：LinguaGo / DeepL / 有道 对比"],
    similar_filler: ["用类似效率工具做跨境邮件翻译"],
    gpm_unknown_filler: ["LinguaGo 文档翻译适合职场人"],
  };
  return pick(texts[def.role]);
}

function buildTikTokPosts(def: CreatorDef, count: number) {
  const posts = [];
  const baseTime = 1789000000;
  for (let i = 1; i <= count; i++) {
    const vid = `tt_video_${padId(def.id)}_${i}`;
    posts.push({
      video_id: vid,
      share_url: `mock://tiktok/video/${padId(def.id)}_${i}`,
      create_time: baseTime + (30 - i) * 86400 + def.id * 100,
      title: evidenceText(def, "tiktok"),
      duration: randInt(25, 90),
      cover_urls: [`mock://cdn/tiktok/cover_${padId(def.id)}_${i}.jpg`],
      region: pick(["US", "SG", "JP", "GB"]),
      hashtag_names:
        def.role === "keyword_mismatch"
          ? pick([
              ["#字幕剪辑", "#影视"],
              ["#雅思", "#托福"],
              ["#AI绘画", "#AIart"],
            ])
          : ["#aitranslation", "#翻译工具", "#跨境"],
      music_info: {
        music_id: `music_${padId(def.id)}_${i}`,
        music_name: "Original Sound",
        author_name: def.display_name,
      },
      stats: {
        play_count: randInt(5000, 150000),
        digg_count: randInt(200, 8000),
        comment_count: randInt(40, 600),
        share_count: randInt(20, 400),
        collect_count: randInt(50, 2000),
      },
    });
  }
  return posts;
}

function buildIgPosts(def: CreatorDef, count: number) {
  const posts = [];
  for (let i = 1; i <= count; i++) {
    const day = String(Math.max(1, 26 - i - (def.id % 5))).padStart(2, "0");
    posts.push({
      id: `ig_media_${padId(def.id)}_${i}`,
      media_url: `mock://instagram/p/${padId(def.id)}_${i}`,
      caption: evidenceText(def, "instagram"),
      permalink: `mock://instagram/p/${padId(def.id)}_${i}`,
      media_type: pick(["VIDEO", "REELS", "CAROUSEL_ALBUM", "IMAGE"] as const),
      like_count: randInt(300, 12000),
      comments_count: randInt(20, 500),
      timestamp: `2026-09-${day}T${String(10 + (i % 8)).padStart(2, "0")}:00:00Z`,
    });
  }
  return posts;
}

function coopPerformance(platform: Platform) {
  const impressions = randInt(200000, 700000);
  const gmv = randInt(3000, 15000);
  const gpm = calcGpm(gmv, impressions);
  return {
    play_count: randInt(20000, 120000),
    engagement_rate: round3(0.04 + rng() * 0.04),
    gmv,
    impressions,
    ...(platform === "tiktok" ? { video_gpm: gpm } : { gpm }),
  };
}

function buildCooperationHistory(def: CreatorDef, platform: Platform) {
  const history: Record<string, unknown>[] = [];

  if (def.role === "own_brand_coop") {
    history.push({
      cooperation_id: `coop_${platform === "tiktok" ? "tt" : "ig"}_${padId(def.id)}_brand_1`,
      brand_name: "LinguaGo AI 翻译",
      product: "AI 翻译工具",
      platform,
      is_current_brand: true,
      product_relation: "own_brand_cooperation",
      exclusivity_risk: "none",
      sample_sent_at: "2026-06-01",
      sample_received_at: "2026-06-03",
      content_published_at: "2026-06-08",
      turnaround_days: 5,
      deliverable: "视频+图文",
      on_time: true,
      revision_count: 1,
      communication_score: 4.6,
      performance: coopPerformance(platform),
      notes: "已与本品牌完成合作，再次触达应排除",
      data_origin: "mock_seed",
    });
  }

  if (
    def.role === "strong_r1" ||
    def.role === "competitor_ended" ||
    (def.role === "strong_r2" && def.id !== 7)
  ) {
    history.push({
      cooperation_id: `coop_${platform === "tiktok" ? "tt" : "ig"}_${padId(def.id)}_other_1`,
      brand_name: pick(["Mock效率本", "Mock跨境助手", "Mock办公AI"]),
      product: pick(["笔记软件", "跨境ERP插件", "会议纪要工具"]),
      platform,
      is_current_brand: false,
      product_relation: "similar_product_user",
      exclusivity_risk: "none",
      sample_sent_at: "2026-07-01",
      sample_received_at: "2026-07-03",
      content_published_at: "2026-07-08",
      turnaround_days: randInt(3, 7),
      deliverable: "视频+图文",
      on_time: true,
      revision_count: randInt(0, 2),
      communication_score: round1(4.5 + rng() * 0.5),
      performance: coopPerformance(platform),
      notes: "样品签收后一周内发布，配合度高",
      data_origin: "mock_seed",
    });
  }

  if (def.role === "competitor_active" || def.id === 10 || def.id === 28) {
    history.push({
      cooperation_id: `coop_${platform === "tiktok" ? "tt" : "ig"}_${padId(def.id)}_comp_active`,
      brand_name: "Mock竞品翻译",
      product: "竞品翻译App",
      platform,
      is_current_brand: false,
      product_relation: "competitor_cooperation_active",
      exclusivity_risk: "possible",
      sample_sent_at: "2026-08-01",
      sample_received_at: "2026-08-02",
      content_published_at: "2026-08-06",
      turnaround_days: 4,
      deliverable: "短视频",
      on_time: true,
      revision_count: 0,
      communication_score: 4.2,
      performance: coopPerformance(platform),
      notes: "竞品合作中，排他条款未知",
      data_origin: "mock_seed",
    });
  }

  if (
    def.role === "competitor_ended" ||
    def.product_relation === "competitor_cooperation_ended"
  ) {
    if (!history.some((h) => h.product_relation === "competitor_cooperation_ended")) {
      history.push({
        cooperation_id: `coop_${platform === "tiktok" ? "tt" : "ig"}_${padId(def.id)}_comp_ended`,
        brand_name: "Mock竞品翻译",
        product: "竞品翻译App",
        platform,
        is_current_brand: false,
        product_relation: "competitor_cooperation_ended",
        exclusivity_risk: "none",
        sample_sent_at: "2026-03-01",
        sample_received_at: "2026-03-03",
        content_published_at: "2026-03-10",
        turnaround_days: 7,
        deliverable: "短视频",
        on_time: true,
        revision_count: 1,
        communication_score: 4.4,
        performance: coopPerformance(platform),
        notes: "竞品合作已结束，可尝试触达",
        data_origin: "mock_seed",
      });
    }
  }

  return history;
}

function productEvidence(def: CreatorDef, platform: Platform, postId: string) {
  if (def.role === "keyword_mismatch") {
    return [
      {
        evidence_id: `ev_${platform === "tiktok" ? "tt" : "ig"}_${padId(def.id)}_1`,
        evidence_type: "organic_post",
        product_name: "LinguaGo AI 翻译",
        product_relation: "category_mentions_only",
        evidence_text: def.mismatch_note ?? "关键词命中但主题不匹配",
        source_post_id: postId,
        confidence: 0.35,
        data_origin: "mock_seed",
      },
    ];
  }
  return [
    {
      evidence_id: `ev_${platform === "tiktok" ? "tt" : "ig"}_${padId(def.id)}_1`,
      evidence_type: "organic_post",
      product_name:
        def.product_relation.includes("competitor")
          ? "Mock竞品翻译"
          : "LinguaGo AI 翻译",
      product_relation: def.product_relation,
      evidence_text: evidenceText(def, platform),
      source_post_id: postId,
      confidence: round2(0.7 + rng() * 0.25),
      data_origin: "mock_seed",
    },
  ];
}

function dataQuality(def: CreatorDef) {
  if (def.role === "audience_unknown") {
    return { audience: "unknown", metrics: "partial", gpm: "unknown" };
  }
  if (def.role === "gpm_unknown_filler") {
    return { audience: "known", metrics: "partial", gpm: "unknown" };
  }
  if (def.role === "new_creator") {
    return { audience: "known", metrics: "known", gpm: "known" };
  }
  return { audience: "known", metrics: "known", gpm: "known" };
}

function buildTikTokCreator(def: CreatorDef) {
  const posts = buildTikTokPosts(def, 3);
  const metrics = metricsFor(def, "tiktok");
  const n = padId(def.id);
  return {
    creator_id: creatorId(def.id),
    display_name: def.display_name,
    is_new_creator: def.role === "new_creator" || def.id === 7,
    platform: "tiktok" as const,
    handle: `@${def.handle_base}`,
    profile: {
      uid: `tt_uid_${n}`,
      unique_id: def.handle_base,
      nickname: def.display_name,
      sec_uid: `MS4wLjABAAAA_mock_${n}`,
      signature: def.topics.join(" · "),
      follower_count: randInt(8000, 280000),
      following_count: randInt(80, 900),
      heart_count: randInt(50000, 2500000),
      video_count: randInt(40, 400),
      verified: def.role === "strong_r1" && def.id <= 3,
      region: pick(["US", "SG", "JP", "GB", "CA"]),
      bio_url: `mock://tiktok/${def.handle_base}`,
      category: pick(["Education", "Tech", "Lifestyle", "Business"]),
      avatar_thumb: `mock://cdn/tiktok/avatar_${n}.jpg`,
    },
    content_topics: def.topics,
    audience: audienceFor(def),
    metrics,
    recent_posts: posts,
    product_usage_evidence: productEvidence(def, "tiktok", posts[0]!.video_id),
    cooperation_history: buildCooperationHistory(def, "tiktok"),
    contact: {
      preferred_channel: "tiktok_dm",
      dm_available: true,
      email: `mock_creator${n}_tt@example.com`,
      consent_status: "unknown",
    },
    data_quality: dataQuality(def),
    scenario_tags: tagsFor(def, "tiktok"),
    expected_ai_signals: expectedSignals(def),
    raw_api_snapshot_ref: `search_tt_${n}`,
    data_origin: "mock_seed",
  };
}

function buildIgCreator(def: CreatorDef) {
  const posts = buildIgPosts(def, 3);
  const metrics = metricsFor(def, "instagram");
  const n = padId(def.id);
  return {
    creator_id: creatorId(def.id),
    display_name: def.display_name,
    is_new_creator: def.role === "new_creator" || def.id === 7,
    platform: "instagram" as const,
    handle: `@${def.handle_base}`,
    profile: {
      ig_id: `ig_uid_${n}`,
      username: def.handle_base,
      name: def.display_name,
      biography: def.topics.join("、"),
      followers_count: randInt(10000, 320000),
      follows_count: randInt(100, 1200),
      media_count: randInt(50, 500),
      website: `mock://instagram/${def.handle_base}`,
      profile_picture_url: `mock://cdn/instagram/avatar_${n}.jpg`,
    },
    content_topics: def.topics,
    audience: audienceFor(def),
    metrics,
    recent_posts: posts,
    product_usage_evidence: productEvidence(def, "instagram", posts[0]!.id),
    cooperation_history: buildCooperationHistory(def, "instagram"),
    contact: {
      preferred_channel: "instagram_dm",
      dm_available: true,
      email: `mock_creator${n}_ig@example.com`,
      consent_status: "unknown",
    },
    data_quality: dataQuality(def),
    scenario_tags: tagsFor(def, "instagram"),
    expected_ai_signals: expectedSignals(def),
    raw_api_snapshot_ref: `search_ig_${n}`,
    data_origin: "mock_seed",
  };
}

function buildSearchSnapshots(platform: Platform, creatorIds: string[]) {
  const prefix = platform === "tiktok" ? "tt" : "ig";
  const success = {
    snapshot_id: `search_${prefix}_001`,
    platform,
    keyword: "AI翻译",
    hashtags:
      platform === "tiktok"
        ? ["#aitranslation", "#翻译工具"]
        : ["#aitranslation", "#productivity"],
    region: "US",
    date_range: { start: "2026-08-01", end: "2026-09-26" },
    total_results: 120,
    returned_creator_ids: creatorIds.slice(0, 8),
    api_response: {
      status: "success" as const,
      status_code: 200,
      request_id: `mock_req_search_${prefix}_001`,
      latency_ms: platform === "tiktok" ? 180 : 210,
      origin: "mock_api_response" as const,
      limitations: ["GPM 需商业授权", "受众画像仅返回聚合数据"],
    },
    data_origin: "mock_api_response" as const,
  };

  const error = {
    snapshot_id: `api_error_${prefix}_001`,
    platform,
    keyword: "AI翻译",
    hashtags: ["#aitranslation"],
    region: "US",
    date_range: { start: "2026-08-01", end: "2026-09-26" },
    total_results: 0,
    returned_creator_ids: [] as string[],
    status: "error" as const,
    status_code: 401,
    request_id: `mock_req_error_${prefix}_001`,
    api_response: {
      status: "error" as const,
      status_code: 401,
      request_id: `mock_req_error_${prefix}_001`,
      latency_ms: 95,
      origin: "mock_api_response" as const,
      limitations: ["OAuth token expired", "data unavailable"],
      error_message: "Unauthorized: OAuth token expired",
    },
    data_origin: "mock_api_response" as const,
    limitations: ["OAuth token expired", "data unavailable"],
  };

  return [success, error];
}

function buildConnectionSnapshots(
  platform: Platform,
  creators: { creator_id: string; handle: string }[],
) {
  const prefix = platform === "tiktok" ? "tt" : "ig";
  const sample = creators.slice(0, 3);
  return sample.map((c, i) => {
    const handle = c.handle.replace("@", "");
    return {
      snapshot_id: `connect_${prefix}_${padId(i + 1)}`,
      platform,
      creator_id: c.creator_id,
      ...(platform === "tiktok"
        ? { unique_id: handle }
        : { username: handle }),
      connected: true,
      api_response: {
        status: "success" as const,
        status_code: 200,
        request_id: `mock_req_connect_${prefix}_${padId(i + 1)}`,
        latency_ms: 200 + i * 20,
        origin: "mock_api_response" as const,
        limitations: ["新视频收录延迟 3-5 分钟", "竞品排他条款不可见"],
      },
      data_origin: "mock_api_response" as const,
    };
  });
}

function meta(platform: Platform) {
  return {
    is_mock: true as const,
    data_origin: "mock_seed" as const,
    platform,
    schema_version: SCHEMA_VERSION,
    seed: SEED,
    generated_at: GENERATED_AT,
    mock_disclaimer: MOCK_DISCLAIMER,
  };
}

interface ValidationStats {
  tt_accounts: number;
  ig_accounts: number;
  unique_creators: number;
  cross_platform: number;
  strong_total: number;
  strong_r1: number;
  keyword_mismatch: number;
  own_brand_coop: number;
  audience_unknown: number;
  gpm_known: number;
  gpm_unknown: number;
  similar_or_competitor_users: number;
  competitor_active: number;
  competitor_ended: number;
  api_errors: number;
  gpm_diff_cross: number;
  new_creators: number;
  coop_efficiency: number;
}

function validate(
  ttCreators: ReturnType<typeof buildTikTokCreator>[],
  igCreators: ReturnType<typeof buildIgCreator>[],
  ttFile: { search_snapshots: { status?: string; api_response: { status: string } }[] },
  igFile: { search_snapshots: { status?: string; api_response: { status: string } }[] },
): ValidationStats {
  const ttIds = new Set(ttCreators.map((c) => c.creator_id));
  const igIds = new Set(igCreators.map((c) => c.creator_id));
  const allIds = new Set([...ttIds, ...igIds]);
  const cross = [...ttIds].filter((id) => igIds.has(id));

  const allAccounts = [...ttCreators, ...igCreators];

  const hasGpm = (c: (typeof allAccounts)[0]) => {
    const m = c.metrics as {
      video_gpm?: number | null;
      gpm_30d?: number | null;
      gpm_origin: string;
    };
    return (
      m.gpm_origin === "mock_seed" &&
      (m.video_gpm != null || m.gpm_30d != null)
    );
  };

  const gpmUnknown = allAccounts.filter(
    (c) => (c.metrics as { gpm_origin: string }).gpm_origin === "unknown",
  ).length;

  const creatorRoles = new Map(CREATOR_DEFS.map((d) => [creatorId(d.id), d]));

  const uniqueByRole = (role: Role) =>
    [...allIds].filter((id) => creatorRoles.get(id)?.role === role).length;

  const similarUsers = [...allIds].filter((id) => {
    const d = creatorRoles.get(id);
    return (
      d &&
      (d.product_relation === "similar_product_user" ||
        d.product_relation === "competitor_user" ||
        d.product_relation === "competitor_cooperation_active" ||
        d.product_relation === "competitor_cooperation_ended")
    );
  }).length;

  const competitorActive = [...allIds].filter((id) => {
    const d = creatorRoles.get(id);
    return d?.product_relation === "competitor_cooperation_active";
  }).length;

  const competitorEnded = [...allIds].filter((id) => {
    const d = creatorRoles.get(id);
    return d?.product_relation === "competitor_cooperation_ended";
  }).length;

  const gpmDiff = CREATOR_DEFS.filter(
    (d) =>
      d.platforms.length === 2 &&
      d.gpm_pair?.tt != null &&
      d.gpm_pair?.ig != null &&
      Math.abs(d.gpm_pair.tt - d.gpm_pair.ig) >= 10,
  ).length;

  const apiErrors = [...ttFile.search_snapshots, ...igFile.search_snapshots].filter(
    (s) => s.api_response.status === "error" || s.status === "error",
  ).length;

  const coopEfficiency = allAccounts.filter((c) =>
    c.scenario_tags.includes("coop_efficiency_known"),
  ).length;

  // count unique creators with coop efficiency (strong_r1)
  const coopEffCreators = [...allIds].filter((id) => {
    const d = creatorRoles.get(id);
    return d?.role === "strong_r1" || (d?.role === "strong_r2" && d.id !== 7);
  }).length;

  return {
    tt_accounts: ttCreators.length,
    ig_accounts: igCreators.length,
    unique_creators: allIds.size,
    cross_platform: cross.length,
    strong_total: uniqueByRole("strong_r1") + uniqueByRole("strong_r2"),
    strong_r1: uniqueByRole("strong_r1"),
    keyword_mismatch: uniqueByRole("keyword_mismatch"),
    own_brand_coop: uniqueByRole("own_brand_coop"),
    audience_unknown: uniqueByRole("audience_unknown"),
    gpm_known: allAccounts.filter(hasGpm).length,
    gpm_unknown: gpmUnknown,
    similar_or_competitor_users: similarUsers,
    competitor_active: competitorActive,
    competitor_ended: competitorEnded,
    api_errors: apiErrors,
    gpm_diff_cross: gpmDiff,
    new_creators: uniqueByRole("new_creator") + (CREATOR_DEFS.some((d) => d.id === 7) ? 1 : 0),
    coop_efficiency: coopEffCreators,
  };
}

function assertStats(s: ValidationStats) {
  const checks: [string, boolean][] = [
    ["TikTok accounts ≥ 20", s.tt_accounts >= 20],
    ["Instagram accounts ≥ 20", s.ig_accounts >= 20],
    ["Unique creators ≥ 30", s.unique_creators >= 30],
    ["Cross-platform ≥ 8", s.cross_platform >= 8],
    ["Fully qualified ≤ 9", s.strong_total <= 9],
    ["Fully qualified ≥ 8", s.strong_total >= 8],
    ["First round ~6", s.strong_r1 === 6],
    ["Keyword mismatch ≥ 5", s.keyword_mismatch >= 5],
    ["Own brand coop ≥ 4", s.own_brand_coop >= 4],
    ["Audience unknown ≥ 4", s.audience_unknown >= 4],
    ["GPM known ≥ 15", s.gpm_known >= 15],
    ["GPM unknown ≥ 5", s.gpm_unknown >= 5],
    ["Similar/competitor users ≥ 6", s.similar_or_competitor_users >= 6],
    ["Competitor active ≥ 2", s.competitor_active >= 2],
    ["Competitor ended ≥ 2", s.competitor_ended >= 2],
    ["API errors ≥ 2", s.api_errors >= 2],
    ["Cross GPM diff ≥ 3", s.gpm_diff_cross >= 3],
    ["New creators ≥ 4", s.new_creators >= 4],
    ["Coop efficiency creators ≥ 6", s.coop_efficiency >= 6],
  ];

  let failed = 0;
  for (const [label, ok] of checks) {
    const mark = ok ? "✓" : "✗";
    console.log(`  ${mark} ${label}`);
    if (!ok) failed++;
  }
  if (failed > 0) {
    throw new Error(`Validation failed: ${failed} check(s) did not pass`);
  }
}

function main() {
  const ttDefs = CREATOR_DEFS.filter((d) => d.platforms.includes("tiktok"));
  const igDefs = CREATOR_DEFS.filter((d) => d.platforms.includes("instagram"));

  const ttCreators = ttDefs.map(buildTikTokCreator);
  const igCreators = igDefs.map(buildIgCreator);

  const ttFile = {
    meta: meta("tiktok"),
    brand: { ...BRAND, platform_preference: [...BRAND.platform_preference] },
    scenario: {
      ...SCENARIO,
      parsed_goal: {
        ...SCENARIO.parsed_goal,
        platform_preference: [...SCENARIO.parsed_goal.platform_preference],
      },
    },
    search_snapshots: buildSearchSnapshots(
      "tiktok",
      ttCreators.map((c) => c.creator_id),
    ),
    account_connection_snapshots: buildConnectionSnapshots(
      "tiktok",
      ttCreators.map((c) => ({ creator_id: c.creator_id, handle: c.handle })),
    ),
    creators: ttCreators,
  };

  const igFile = {
    meta: meta("instagram"),
    brand: { ...BRAND, platform_preference: [...BRAND.platform_preference] },
    scenario: {
      ...SCENARIO,
      parsed_goal: {
        ...SCENARIO.parsed_goal,
        platform_preference: [...SCENARIO.parsed_goal.platform_preference],
      },
    },
    search_snapshots: buildSearchSnapshots(
      "instagram",
      igCreators.map((c) => c.creator_id),
    ),
    account_connection_snapshots: buildConnectionSnapshots(
      "instagram",
      igCreators.map((c) => ({ creator_id: c.creator_id, handle: c.handle })),
    ),
    creators: igCreators,
  };

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const ttPath = path.join(OUT_DIR, "tiktok_creators.json");
  const igPath = path.join(OUT_DIR, "instagram_creators.json");

  fs.writeFileSync(ttPath, JSON.stringify(ttFile, null, 2) + "\n", "utf8");
  fs.writeFileSync(igPath, JSON.stringify(igFile, null, 2) + "\n", "utf8");

  const stats = validate(ttCreators, igCreators, ttFile, igFile);

  console.log("\n=== Mock data generation complete ===");
  console.log(`Seed: ${SEED}`);
  console.log(`Wrote: ${ttPath}`);
  console.log(`Wrote: ${igPath}`);
  console.log("\nStats:");
  console.log(JSON.stringify(stats, null, 2));
  console.log("\nValidation:");
  assertStats(stats);
  console.log("\nAll checks passed.");
}

main();
