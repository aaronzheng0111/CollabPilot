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
  creator_011: { tiktok: ["字幕剪辑｜《黑袍纠察队》名场面中英双字幕，这不是AI翻译工具测评", "影视字幕组翻得太神了｜高能剪辑合集，不谈翻译App", "美剧熟肉搬运：本周最火片段｜纯字幕剪辑教程"] },
  creator_012: { tiktok: ["四级翻译题高频句式30个，背完稳过｜应试技巧不是AI翻译工具", "考研英语翻译大题万能模板，直接套用｜备考向", "雅思翻译练习：同义替换怎么找｜考试翻译≠产品使用"] },
  creator_013: { tiktok: ["Midjourney画赛博朋克｜提示词不用翻译工具也能出图", "AI绘画上色教程：从线稿到成图只要5分钟｜不谈翻译产品", "Stable Diffusion人像LoRA推荐｜开箱素材包不是翻译App"] },
  creator_014: { instagram: ["美研申请时间线：文书别用机翻翻译腔｜留学申请辅导不是AI翻译工具", "个人陈述怎么写出特色？我拿到3个offer的文书思路｜非翻译产品测评", "选校清单怎么定：冲刺、匹配、保底｜不谈翻译App开箱"] },
  creator_015: { instagram: ["日语N2翻译题备考60天｜考试翻译≠AI翻译工具使用分享", "韩语TOPIK作文高分句型20条｜备考向，不是翻译产品", "法语DELF B1口语真题练习｜语言考试，非翻译App测评"] },
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
  creator_011: ["#影视剪辑", "#双语字幕"],
  creator_012: ["#英语四级", "#考研英语"],
  creator_013: ["#AI绘画", "#midjourney"],
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

/** Mutates `file.creators` and returns the serialized file with renames applied. */
export function applyScenarioOverrides(file: Json, platform: Platform): string {
  const byId = new Map<string, Json>(file.creators.map((c: Json) => [c.creator_id, c]));
  const replacements: [string, string][] = [];

  for (const c of file.creators) {
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
