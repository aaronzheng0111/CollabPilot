/**
 * Scenario overrides applied after the seeded generator builds each file.
 *
 * - Neutral display names and handles: names must not reveal the expected verdict.
 * - Hand-written posts per creator: the model has to read content to judge fit,
 *   and drafts need distinct material to quote.
 * - Post dates relative to 2026-09-26: creator_007–009 post only 40–73 days ago,
 *   so a 30-day search window misses them and a 90-day window finds them.
 * - Borderline creators get concrete reasons to be `pending`, keeping the
 *   expected first-round fit at about 6/10. Demo auto-retry is capped at 0 so
 *   the shortfall stays visible; a manual/window retry can still surface 007–009.
 */

type Platform = "tiktok" | "instagram";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;

const ANCHOR_MS = Date.UTC(2026, 8, 26, 12, 0, 0);
const DAY_MS = 86_400_000;

const RENAME: Record<string, [string, string]> = {
  creator_007: ["Grace译", "grace.yi"],
  creator_010: ["Jake聊翻译", "jake.talks"],
  creator_016: ["Paula译日常", "paula.daily"],
  creator_017: ["Quinn效率", "quinn.works"],
  creator_018: ["Rita跨境译", "rita.xborder"],
  creator_019: ["Sam出海笔记", "sam.goglobal"],
  creator_020: ["Tina工具箱", "tina.toolbox"],
  creator_021: ["Uma译记", "uma.notes"],
  creator_022: ["Vince跨境", "vince.xb"],
  creator_023: ["Wendy留学译", "wendy.abroad"],
  creator_024: ["Xander译", "xander.yi"],
  creator_025: ["Yuna工具", "yuna.tools"],
  creator_026: ["Zack跨境", "zack.xb"],
  creator_027: ["Ava术语", "ava.terms"],
  creator_028: ["Blair译评", "blair.reviews"],
  creator_029: ["Chris翻译对比", "chris.compare"],
  creator_030: ["Dana吐槽工具", "dana.rants"],
  creator_031: ["Eli工具控", "eli.gear"],
  creator_032: ["Faye横评", "faye.bench"],
  creator_033: ["Gus出海", "gus.global"],
  creator_034: ["Holly译站", "holly.station"],
};

const POSTS: Record<string, Partial<Record<Platform, string[]>>> = {
  creator_001: {
    tiktok: ["用LinguaGo实时对话翻译和日本供应商开视频会，全程没卡壳", "中英日韩四语菜单，LinguaGo拍照翻译一秒出结果", "跨境客服话术怎么翻得地道？我的LinguaGo术语表分享"],
    instagram: ["出差东京第3天，靠LinguaGo实时翻译搞定地铁问路和点餐", "LinguaGo对话模式实测：日语转中文延迟不到1秒", "跨境人的翻译工具箱：我每天用的3个LinguaGo功能"],
  },
  creator_002: {
    tiktok: ["亚马逊Listing多语种上架，LinguaGo批量翻译省了半天", "对比3款翻译工具写商品描述，LinguaGo术语最稳", "跨境卖家必看：用LinguaGo翻译买家差评再回复"],
    instagram: ["独立站德语法语页面，我用LinguaGo文档翻译一次导出", "跨境选品周报｜本周用LinguaGo翻了40份供应商报价", "从英文邮件到西语客服，LinguaGo帮我统一了话术"],
  },
  creator_003: {
    tiktok: ["外企周报中译英，LinguaGo保留了原来的表格格式", "整份PPT拖进LinguaGo，20页英文版10分钟出", "职场邮件别再机翻腔：LinguaGo语气调节实测"],
    instagram: ["打工人效率｜合同附件PDF用LinguaGo翻译后直接批注", "跨部门会议纪要双语版，我的LinguaGo模板", "入职外企第一年，文档翻译我只用LinguaGo"],
  },
  creator_004: {
    tiktok: ["留学生看病实录：LinguaGo实时对话翻译帮我和医生沟通", "租房签约别踩坑，用LinguaGo逐条翻译英文租约", "教授office hour前，我用LinguaGo练了一遍对话"],
    instagram: ["英国留学第一周，银行开户全靠LinguaGo对话翻译", "小组作业跨国队友沟通，LinguaGo中英实时字幕", "留学生必备App清单：LinguaGo排第一的原因"],
  },
  creator_005: {
    tiktok: ["法律合同翻译最怕术语不统一，LinguaGo术语库实测", "建了200条外贸术语库，导入LinguaGo后译文终于一致", "合同条款中译英：LinguaGo初译和人工校对耗时对比"],
    instagram: ["术语库搭建教程｜LinguaGo导入Excel词表三步完成", "律所实习生的合同翻译流程：LinguaGo初译加人工复核", "医疗器械说明书翻译，LinguaGo术语锁定功能救了我"],
  },
  creator_006: {
    tiktok: ["5款AI翻译横评：长文档场景LinguaGo格式保留最好", "实时对话翻译延迟实测：LinguaGo、DeepL、谷歌翻译", "我给AI翻译工具打分：LinguaGo术语库是加分项"],
    instagram: ["效率工具月度测评｜翻译类：LinguaGo本月主力使用", "测评不收钱：LinguaGo哪些地方还不够好", "AI翻译工具选购指南：学生党和职场人怎么选"],
  },
  creator_007: {
    tiktok: ["日本交换生活记录：LinguaGo帮我看懂区役所通知", "和房东日语沟通不再尴尬，LinguaGo对话模式", "留学生开学准备：我装的第一个App是LinguaGo"],
    instagram: ["交换生vlog｜用LinguaGo翻译课程大纲", "日语课听不懂？LinguaGo实时字幕陪我上课", "留学行李清单之外，手机里必装LinguaGo"],
  },
  creator_008: {
    tiktok: ["韩国工厂验货，LinguaGo中韩实时翻译现场沟通", "中日韩三语报价单，LinguaGo一次翻完", "跨境办公小技巧：LinguaGo翻译韩文聊天截图"],
    instagram: ["首尔出差日记｜LinguaGo陪我谈下第一个供应商", "日韩客户邮件模板，用LinguaGo批量生成双语版", "外贸新人如何快速处理日文询盘：我的LinguaGo流程"],
  },
  creator_009: {
    tiktok: ["每周读10篇英文行业报告，我用LinguaGo双语对照", "LinguaGo文档翻译加笔记软件，搭建我的外文知识库", "英文会议录音转文字再翻译，LinguaGo一站完成"],
    instagram: ["效率博主的翻译工作流：LinguaGo加日历提醒", "英文论文精读法：LinguaGo段落对照翻译", "我的年度效率工具：LinguaGo文档翻译用了300次"],
  },
  creator_010: {
    tiktok: ["竞品翻译笔开箱：扫描翻译速度实测，本期不谈本品", "合作款翻译笔开箱翻车记录：续航虚标", "翻译工具怎么选？我目前在用合作竞品的方案"],
    instagram: ["合作｜竞品翻译新功能开箱，体验码在主页", "和Mock竞品翻译合作第4个月：开箱与吐槽", "旅行翻译神器开箱（竞品合作，非本品）"],
  },
  creator_011: {
    tiktok: [
      "春夏季日常妆教｜5分钟通勤妆完整步骤",
      "平价口红试色合集｜黄皮显白三支推荐",
      "护肤测评｜百元水乳够用吗？纯护肤分享",
    ],
  },
  creator_012: {
    tiktok: [
      "黄皮口红试色｜豆沙色vs裸粉实测对比",
      "底妆卡粉怎么办｜三步服帖技巧分享",
      "彩妆好物开箱｜本月回购的平价彩妆",
    ],
  },
  creator_013: {
    tiktok: [
      "晚间护肤routine｜敏感肌也能用的水乳顺序",
      "夏日防晒怎么选｜清爽不搓泥实测",
      "化妆刷清洁保养｜一周一次就够了",
    ],
  },
  creator_014: {
    instagram: [
      "新手彩妆教程｜十步画出通勤烟熏眼",
      "眼影盘横评｜大地色盘日常怎么画",
      "美甲灵感｜春夏显白短款款式合集",
    ],
  },
  creator_015: {
    instagram: [
      "化妆品测评｜这瓶精华液用了30天真实反馈",
      "精华液层叠顺序｜先薄后厚不踩雷",
      "卸妆好物分享｜温和不糊眼的卸妆油",
    ],
  },
  creator_016: { tiktok: ["LinguaGo合作视频已发布，感谢品牌寄样", "上次合作后继续用LinguaGo做视频字幕翻译", "粉丝问我LinguaGo好不好用，统一回复在这"] },
  creator_017: { tiktok: ["和LinguaGo的合作款：职场翻译3个技巧", "LinguaGo文档翻译日常使用记录", "效率工具桌面整理，翻译用LinguaGo"] },
  creator_018: { instagram: ["LinguaGo品牌合作｜跨境客服多语回复", "合作结束后我还在用LinguaGo翻译邮件", "跨境人一周工作流，翻译环节交给LinguaGo"] },
  creator_019: { instagram: ["感谢LinguaGo邀请合作，出海翻译实测", "出海团队多语文档，用LinguaGo统一翻译", "海外社媒运营：用LinguaGo翻译评论区"] },
  creator_020: { tiktok: ["试了一款AI翻译App，拍照翻译很快", "工具箱更新：本周收藏的3个翻译工具", "用AI翻译做旅行攻略，外文景点介绍秒懂"] },
  creator_021: { tiktok: ["LinguaGo翻译跨境邮件，语气比之前自然", "用LinguaGo写英文产品说明书初稿", "我的翻译记录本：LinguaGo常用短语收藏"] },
  creator_022: { instagram: ["跨境职场人用AI翻译处理英文周报", "对比两款翻译工具写商务邮件", "AI翻译会取代外贸翻译吗？我的看法"] },
  creator_023: { instagram: ["留学生活｜AI翻译帮我读懂保险条款", "图书馆打卡：用翻译工具精读英文文献", "留学生常用翻译App分享"] },
  creator_024: { tiktok: ["第一次测评LinguaGo实时对话翻译", "周末探店：城南新开的咖啡馆", "开箱新入的机械键盘"] },
  creator_025: { tiktok: ["第一次用LinguaGo翻译英文说明书，比预想好用", "我的桌面好物分享", "健身第30天打卡"] },
  creator_026: { instagram: ["新号第一条：用LinguaGo翻译供应商报价", "义乌市场逛吃记录", "新入手的相机试拍"] },
  creator_027: { instagram: ["刚开始整理术语表，试了LinguaGo的术语库", "考研自习室日常", "秋天穿搭分享"] },
  creator_028: { tiktok: ["本月继续和Mock竞品翻译合作：同传功能深度测评", "Mock竞品翻译会员值不值？合作期真实体验", "翻译App深度对比（本期由Mock竞品翻译赞助）"] },
  creator_029: { instagram: ["和Mock竞品翻译的合作结束了，聊聊这一年的感受", "最近在找新的翻译工具，评论区求推荐", "出差用手机拍照翻译菜单，几款App都试了"] },
  creator_030: { tiktok: ["竞品翻译吐槽：合同术语错得离谱，别再被坑", "翻译App开箱翻车：会员自动续费的坑，大家注意", "为什么我不再相信某竞品AI翻译的专业版｜吐槽向"] },
  creator_031: { instagram: ["一直爱用Mock竞品翻译，体验很好", "Mock竞品翻译新功能：离线包实测", "我的翻译工具只认这一个（非广告）"] },
  creator_032: { tiktok: ["五款翻译工具横评：LinguaGo、DeepL、有道对比", "翻译工具横评第二期：长文档格式保留", "本期由Mock竞品翻译合作支持：同传功能测评"] },
  creator_033: { instagram: ["用类似效率工具做跨境邮件翻译", "出海创业第2年：团队怎么解决多语沟通", "海外展会实录：翻译耳机好不好用"] },
  creator_034: { tiktok: ["LinguaGo文档翻译适合职场人", "五一去大理的旅行vlog", "我的读书笔记：本月看完的4本书"] },
};

const HASHTAGS: Record<string, string[]> = {
  creator_011: ["#妆教", "#护肤", "#口红", "#护肤测评"],
  creator_012: ["#口红", "#底妆", "#彩妆好物"],
  creator_013: ["#护肤", "#防晒", "#化妆刷"],
};

/** Idle/main table reads profile.category + content_topics — force 美妆 for mismatch demos. */
const BEAUTY_MISMATCH: Record<string, { topics: string[]; product: string }> = {
  creator_011: { topics: ["护肤", "口红", "妆教", "测评化妆品"], product: "Mock 平价口红" },
  creator_012: { topics: ["口红试色", "底妆", "彩妆好物"], product: "Mock 口红试色盘" },
  creator_013: { topics: ["护肤routine", "防晒", "化妆刷"], product: "Mock 防晒霜" },
  creator_014: { topics: ["彩妆教程", "眼影盘", "美甲"], product: "Mock 眼影盘" },
  creator_015: { topics: ["化妆品测评", "精华液", "卸妆"], product: "Mock 精华液" },
};

const WINDOW_OUTSIDE = new Set(["creator_007", "creator_008", "creator_009"]);
const SINGLE_RELATED = new Set(["creator_024", "creator_025", "creator_026", "creator_027", "creator_034"]);

const WINDOW_REASON = "相关内容都发布于 30 天前；放宽时间窗口后可进入二轮名单";
const SINGLE_REASON = "近 30 天只有 1 条本品相关内容，持续性不足；无历史合作";

const SIGNALS: Record<string, [string, string]> = {
  creator_007: ["recommend_after_relax", WINDOW_REASON],
  creator_008: ["recommend_after_relax", WINDOW_REASON],
  creator_009: ["recommend_after_relax", WINDOW_REASON],
  creator_024: ["review", SINGLE_REASON],
  creator_025: ["review", SINGLE_REASON],
  creator_026: ["review", SINGLE_REASON],
  creator_027: ["review", SINGLE_REASON],
  creator_029: ["review", "未见使用本品的证据；与竞品合作的结束时间与排他期未知"],
  creator_030: ["review", "内容以吐槽竞品为主，未见使用本品的证据"],
  creator_032: ["review", "横评包含本品，但与竞品的合作进行中，排他条款未知"],
  creator_034: ["review", "只有 1 条本品相关内容，持续性不足；GPM 未知"],
};

const EXTRA_TAGS: Record<string, string[]> = {
  creator_007: ["window_outside_30d"],
  creator_008: ["window_outside_30d"],
  creator_009: ["window_outside_30d"],
  creator_024: ["single_related_post"],
  creator_025: ["single_related_post"],
  creator_026: ["single_related_post"],
  creator_027: ["single_related_post"],
  creator_034: ["single_related_post"],
  creator_029: ["no_own_brand_evidence"],
  creator_030: ["no_own_brand_evidence"],
  creator_032: ["competitor_active", "competitor_exclusivity_unknown"],
};

function agesFor(creatorId: string, platform: Platform): number[] {
  const n = Number(creatorId.slice(-3));
  const k = (n % 3) + (platform === "instagram" ? 1 : 0);
  if (WINDOW_OUTSIDE.has(creatorId)) return [40 + k, 55 + k, 70 + k];
  if (SINGLE_RELATED.has(creatorId)) return [5, 9, 14];
  return [1 + k, 4 + k, 8 + k];
}

function setTime(post: Json, platform: Platform, ageDays: number): void {
  const when = ANCHOR_MS - ageDays * DAY_MS;
  if (platform === "tiktok") {
    post.create_time = Math.floor(when / 1000);
  } else {
    post.timestamp = new Date(when).toISOString().replace(".000Z", "Z");
  }
}

function fixCreator(c: Json, platform: Platform, byId: Map<string, Json>): void {
  const cid: string = c.creator_id;
  const texts = POSTS[cid][platform] as string[];
  const ages = agesFor(cid, platform);
  const textKey = platform === "tiktok" ? "title" : "caption";

  c.recent_posts.forEach((post: Json, i: number) => {
    const text = texts[i];
    post[textKey] = text;
    setTime(post, platform, ages[i]);
    if (platform === "tiktok" && HASHTAGS[cid]) post.hashtag_names = HASHTAGS[cid];
    if (platform === "tiktok" && SINGLE_RELATED.has(cid) && !text.includes("LinguaGo")) {
      post.hashtag_names = ["#日常"];
    }
  });

  // Keyword-mismatch demos: table columns must read as 美妆, not translation.
  if (BEAUTY_MISMATCH[cid]) {
    const { topics, product } = BEAUTY_MISMATCH[cid];
    c.content_topics = topics;
    c.profile.category = "Beauty";
    if (platform === "tiktok") {
      c.profile.signature = topics.join(" · ");
    } else {
      c.profile.biography = topics.join("、");
    }
    if (c.audience?.status === "known") {
      c.audience.interests = topics;
    }
    for (const ev of c.product_usage_evidence ?? []) {
      ev.product_name = product;
      ev.product_relation = "category_mentions_only";
    }
  }

  const postText = new Map<string, string>(
    c.recent_posts.map((p: Json) => [p.video_id ?? p.id, p.title ?? p.caption]),
  );
  for (const ev of c.product_usage_evidence) {
    ev.evidence_text = postText.get(ev.source_post_id);
  }

  if (SINGLE_RELATED.has(cid)) {
    const countKey = platform === "tiktok" ? "video_count" : "media_count";
    c.profile[countKey] = 9 + (Number(cid.slice(-3)) % 7);
  }

  if (SIGNALS[cid]) {
    const [hint, reason] = SIGNALS[cid];
    c.expected_ai_signals.expected_decision_hint = hint;
    c.expected_ai_signals.expected_reason = reason;
  }
  for (const tag of EXTRA_TAGS[cid] ?? []) {
    if (!c.scenario_tags.includes(tag)) c.scenario_tags.push(tag);
  }

  if (cid === "creator_032") {
    const template = structuredClone(byId.get("creator_028").cooperation_history[0]);
    template.cooperation_id = "coop_tt_032_comp_1";
    template.content_published_at = "2026-09-12";
    template.sample_sent_at = "2026-09-02";
    template.sample_received_at = "2026-09-04";
    c.cooperation_history = [template];
  }
}

/**
 * Beauty-camera demo cohort. Keyword search for 「美妆」 or 「AI美颜相机」
 * hits exactly these six. 101–103 are on-style beauty creators with a known
 * audience. 104–105 post about the camera but the platform has no audience
 * profile. 106 is an AI-tool reviewer: the product name appears so the
 * keyword hits, and the posts say a beauty camera does not fit the channel.
 */
const BEAUTY_CAMERA: Array<{
  id: string;
  name: string;
  handle: string;
  topics: string[];
  category: string;
  signature: string;
  audienceKnown: boolean;
  posts: string[];
  productName: string;
}> = [
  {
    id: "creator_101",
    name: "林晚妆",
    handle: "lin.wanzhuang",
    topics: ["美妆", "妆教", "AI美颜相机"],
    category: "Beauty",
    signature: "美妆妆教 · 日常用 AI美颜相机 出片",
    audienceKnown: true,
    productName: "AI美颜相机",
    posts: [
      "通勤妆实测｜AI美颜相机原相机对比，皮肤光泽很自然",
      "美妆博主的拍照流程：先上妆，再用AI美颜相机出片",
      "黄皮妆教｜AI美颜相机把法令纹磨淡了，眉毛还在",
    ],
  },
  {
    id: "creator_102",
    name: "苏小柔",
    handle: "su.xiaorou",
    topics: ["美妆", "自拍", "AI美颜相机"],
    category: "Beauty",
    signature: "美妆自拍 · AI美颜相机夜景人像",
    audienceKnown: true,
    productName: "AI美颜相机",
    posts: [
      "自拍党一周｜AI美颜相机夜景人像不假白",
      "美妆分享：底妆没拍好，我用AI美颜相机补了高光",
      "素颜到上妆全程记录，最后一张是AI美颜相机直出",
    ],
  },
  {
    id: "creator_103",
    name: "何清清",
    handle: "he.qingqing",
    topics: ["美妆", "护肤", "AI美颜相机"],
    category: "Beauty",
    signature: "美妆护肤 · 视频都用 AI美颜相机",
    audienceKnown: true,
    productName: "AI美颜相机",
    posts: [
      "护肤后立刻拍｜AI美颜相机保留了毛孔，没有塑料脸",
      "美妆教程第12期：眼妆特写用AI美颜相机对焦很稳",
      "粉丝问相机｜我日常妆容视频都用AI美颜相机拍的",
    ],
  },
  {
    id: "creator_104",
    name: "周可儿",
    handle: "zhou.keer",
    topics: ["美妆", "AI美颜相机"],
    category: "Beauty",
    signature: "美妆开箱 · AI美颜相机",
    audienceKnown: false,
    productName: "AI美颜相机",
    posts: [
      "今日妆容｜AI美颜相机拍的口红试色",
      "美妆vlog：出门前用AI美颜相机检查脸部高光",
      "新买的AI美颜相机，拿来拍美妆开箱",
    ],
  },
  {
    id: "creator_105",
    name: "马晓宁",
    handle: "ma.xiaoning",
    topics: ["美妆", "底妆", "AI美颜相机"],
    category: "Beauty",
    signature: "美妆小白 · AI美颜相机前置",
    audienceKnown: false,
    productName: "AI美颜相机",
    posts: [
      "底妆测评｜AI美颜相机把粉感拍得很清楚",
      "美妆小白跟练：AI美颜相机前置镜头教程",
      "这支粉底在AI美颜相机里会不会假白",
    ],
  },
  {
    id: "creator_106",
    name: "韩测测",
    handle: "han.review",
    topics: ["AI测评", "效率工具", "编程助手"],
    category: "Tech",
    signature: "AI工具测评 · 效率 · 编程，不拍妆",
    audienceKnown: true,
    productName: "AI效率工具",
    posts: [
      "AI测评周报｜代码助手和文档模型。顺手提一句AI美颜相机：这是美妆道具，完全不是我这种工具频道的风格",
      "效率博主不拍妆｜有人让我评AI美颜相机，我和美妆内容不搭，这条只记录为什么拒掉",
      "编程向AI测评：终端和IDE插件。美颜相机、美妆滤镜不在我的测评清单里",
    ],
  },
];

function beautyCameraCreator(template: Json, spec: (typeof BEAUTY_CAMERA)[number]): Json {
  const creator = structuredClone(template);
  const n = spec.id.slice(-3);
  creator.creator_id = spec.id;
  creator.display_name = spec.name;
  creator.handle = `@${spec.handle}`;
  creator.profile.uid = `tt_uid_${n}`;
  creator.profile.unique_id = spec.handle;
  creator.profile.nickname = spec.name;
  creator.profile.sec_uid = `MS4wLjABAAAA_mock_${n}`;
  creator.profile.signature = spec.signature;
  creator.profile.bio_url = `mock://tiktok/${spec.handle}`;
  creator.profile.category = spec.category;
  creator.profile.avatar_thumb = `mock://cdn/tiktok/avatar_${n}.jpg`;
  creator.content_topics = spec.topics;
  creator.audience = spec.audienceKnown
    ? {
        status: "known",
        age_range: "18-24",
        gender: "female_60",
        regions: ["中国大陆"],
        interests: spec.topics.slice(0, 3),
        note: null,
      }
    : {
        status: "unknown",
        age_range: null,
        gender: null,
        regions: null,
        interests: null,
        note: "平台未公开受众画像，数据缺失",
      };
  if (!spec.audienceKnown) {
    creator.metrics = {
      ...creator.metrics,
      gmv_30d: null,
      impressions_30d: null,
      currency: "unknown",
      units_sold_30d: null,
      gmv_per_buyer: null,
      gpm_origin: "unknown",
      video_gpm: null,
    };
    creator.data_quality = { audience: "unknown", metrics: "partial", gpm: "unknown" };
  } else {
    creator.data_quality = { audience: "known", metrics: "known", gpm: "known" };
  }
  creator.recent_posts = spec.posts.map((title, index) => {
    const post = structuredClone(creator.recent_posts[Math.min(index, creator.recent_posts.length - 1)]);
    const ageDays = [3, 8, 14][index] ?? 14;
    post.video_id = `tt_video_${n}_${index + 1}`;
    post.share_url = `mock://tiktok/video/${n}_${index + 1}`;
    post.title = title;
    post.create_time = Math.floor(ANCHOR_MS / 1000) - ageDays * 86_400;
    post.hashtag_names = spec.topics.map((topic) => `#${topic}`);
    post.music_info = {
      ...(post.music_info ?? {}),
      music_id: `music_${n}_${index + 1}`,
      author_name: spec.name,
    };
    return post;
  });
  creator.product_usage_evidence = [
    {
      evidence_id: `ev_tt_${n}_1`,
      evidence_type: "organic_post",
      product_name: spec.productName,
      product_relation: spec.audienceKnown && spec.category === "Beauty" ? "own_brand_user" : "category_mentions_only",
      evidence_text: spec.posts[0],
      source_post_id: `tt_video_${n}_1`,
      confidence: spec.category === "Beauty" ? 0.9 : 0.2,
      data_origin: "mock_seed",
    },
  ];
  creator.cooperation_history = [];
  creator.contact = {
    preferred_channel: "tiktok_dm",
    dm_available: true,
    email: `mock_${spec.handle.replace(/\./g, "_")}@example.com`,
    consent_status: "unknown",
  };
  creator.scenario_tags = spec.category === "Tech" ? ["keyword_mismatch"] : spec.audienceKnown ? ["beauty_camera_fit"] : ["audience_unknown"];
  creator.expected_ai_signals = {
    expected_decision_hint: spec.category === "Tech" ? "reject" : spec.audienceKnown ? "recommend" : "review",
    expected_reason:
      spec.category === "Tech"
        ? "关键词命中 AI美颜相机，内容是 AI 工具测评，美妆道具不符合频道风格"
        : spec.audienceKnown
          ? "持续发布美妆内容并实际使用 AI美颜相机"
          : "内容相关，但平台未公开受众画像",
  };
  creator.raw_api_snapshot_ref = `search_tt_${n}`;
  return creator;
}

function injectBeautyCameraCohort(file: Json, platform: Platform): void {
  if (platform !== "tiktok") return;
  if (file.creators.some((creator: Json) => creator.creator_id === "creator_101")) return;
  const template = file.creators.find((creator: Json) => creator.creator_id === "creator_011");
  for (const spec of BEAUTY_CAMERA) file.creators.push(beautyCameraCreator(template, spec));
}

/** Mutates `file.creators` and returns the serialized file with renames applied. */
export function applyScenarioOverrides(file: Json, platform: Platform): string {
  const byId = new Map<string, Json>(file.creators.map((c: Json) => [c.creator_id, c]));
  const replacements: [string, string][] = [];

  injectBeautyCameraCohort(file, platform);
  for (const c of file.creators) {
    if (!POSTS[c.creator_id]) continue;
    fixCreator(c, platform, byId);
    const rename = RENAME[c.creator_id];
    if (rename) {
      const oldHandle = c.profile.unique_id ?? c.profile.username;
      replacements.push([c.display_name, rename[0]]);
      replacements.push([oldHandle, rename[1]]);
    }
  }

  let text = JSON.stringify(file, null, 2) + "\n";
  replacements.sort((a, b) => b[0].length - a[0].length);
  for (const [oldValue, newValue] of replacements) {
    text = text
      .replaceAll(`"${oldValue}"`, `"${newValue}"`)
      .replaceAll(`@${oldValue}"`, `@${newValue}"`)
      .replaceAll(`/${oldValue}"`, `/${newValue}"`);
  }
  JSON.parse(text);
  return text;
}
