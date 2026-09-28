from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from collabpilot.agent.context import ContextBuilder
from collabpilot.agent.runtime import AgentRuntime, EventHandler, RuntimeEvent
from collabpilot.campaign import mock_store
from collabpilot.campaign.decisions import DecisionResult, approve_pending
from collabpilot.campaign.goal import (
    CONFIRM_ASSUMPTIONS,
    GOAL_ORIGIN,
    MAX_GRILL_ROUNDS,
    REQUIRED_KEYS,
    Campaign,
    ParsedGoal,
    apply_user_cooperated_preference,
    build_grill,
    extract_json_block,
    ground_goal_in_user_text,
    render_clarifying_reply,
    render_invalid_reply,
    render_parsed_reply,
    strip_json_blocks,
    validate_grill,
    validate_parsed_goal,
)
from collabpilot.campaign.audience import AUDIENCE_OVERRIDE, apply_audience_overrides
from collabpilot.campaign.store import CampaignStore
from collabpilot.campaign.workbench import WorkbenchState, build_workbench_state
from collabpilot.campaign.selection import fingerprint_goal, queue_exclude_creator, queue_save_selection
from collabpilot.campaign.channels import pick_channel, queue_confirm_channel
from collabpilot.campaign.drafts import (
    DraftBatch,
    NEED_SELECTION,
    NEED_THREE_CREATORS,
    PICK_CREATOR_FOR_DRAFT,
    SAVE_DRAFTS,
    apply_approve_draft,
    apply_reject_draft,
    draft_prerequisites,
    drafts_payload,
    outreach_ids,
    queue_save_drafts,
    render_drafts_message,
    render_drafts_prompt,
    resolve_channels,
    validate_drafts,
)
from collabpilot.campaign.follow_up import (
    FollowUpBatch,
    apply_note_follow_up,
    follow_up_payload,
    follow_up_prerequisites,
    queue_save_follow_up,
    render_follow_up_message,
    render_follow_up_prompt,
    validate_follow_up,
)
from collabpilot.campaign.topic_match import (
    TopicRejected,
    fit_creator_ids,
    ids_excluded_from_judgment,
    lock_topic_rejections,
    locked_rule_note,
    rejudge_note,
    skipped_locked_note,
    validate_topic_verdicts,
)
from collabpilot.campaign.retry import (
    MAX_AUTO_RETRIES,
    MODEL_STRATEGY_REQUIRED,
    RETRY_STEP,
    StrategyOutcome,
    accept_retry_strategy,
    append_search_round,
    build_round_summary,
    fit_count,
    is_insufficient,
    parse_retry_strategy,
    queue_accept_short_list,
    refresh_accept_short_list,
    render_retry_message,
    render_strategy_failure,
    render_strategy_reply,
    target_count,
)
from collabpilot.campaign.verdict import (
    EVALUATE_STEP,
    LLM_LABEL,
    ModelUnavailable,
    RejectedVerdict,
    VerdictBatch,
    render_campaign_prompt,
    render_candidates_message,
    retain_prior_fits,
    sort_verdicts,
    validate_verdicts,
)
from collabpilot.domain.errors import MissingApiKeyError, ProviderError
from collabpilot.domain.models import (
    ChatResult,
    Message,
    ModelResponse,
    ProjectSummary,
    StoredMessage,
)
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.observability.logging import get_logger
from collabpilot.providers.base import Provider
from collabpilot.providers.registry import ProviderRegistry
from collabpilot.settings import PROJECT_ROOT, AgentSettings
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.get_creator import GetCreatorTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool
from collabpilot.tools.base import ToolContext


GOAL_PROMPT_RELATIVE = "config/prompts/goal.md"
CAMPAIGN_PROMPT_RELATIVE = "config/prompts/campaign.md"
RETRY_PROMPT_RELATIVE = "config/prompts/retry.md"
DRAFTS_PROMPT_RELATIVE = "config/prompts/drafts.md"
FOLLOW_UP_PROMPT_RELATIVE = "config/prompts/follow_up.md"
# Campaign tools that must not run before the goal is PARSED.
SEARCH_TOOLS = frozenset(
    {SearchCreatorsTool.name, GetCreatorTool.name, ApplyHardFiltersTool.name}
)
CONFIRM_WORDS = frozenset(
    {"确认", "确定", "同意", "批准", "好", "好的", "可以", "ok", "yes", "y"}
)
GENERATE_DRAFTS_PHRASES = ("生成草稿", "写草稿", "起草邀请", "生成邀请草稿")


def is_confirmation(text: str) -> bool:
    return text.strip().strip("。！!.").lower() in CONFIRM_WORDS


def is_generate_drafts_request(text: str) -> bool:
    cleaned = text.strip().strip("。！!.")
    if cleaned in GENERATE_DRAFTS_PHRASES:
        return True
    return any(phrase in cleaned for phrase in GENERATE_DRAFTS_PHRASES)


def drafts_missing_message(error_code: str | None) -> str:
    if error_code in (NEED_SELECTION, NEED_THREE_CREATORS):
        return PICK_CREATOR_FOR_DRAFT
    if error_code:
        return f"还不能生成草稿：{error_code}。"
    return PICK_CREATOR_FOR_DRAFT


def needs_evaluation(campaign: Campaign) -> bool:
    """A filtered candidate set needing a fresh judgment → run the judgment step.

    Stage ``EVALUATING`` means hard-filter just ran (possibly retaining prior
    fits); we still need a new model pass even when some fit rows remain.
    """
    return (
        campaign.goal_status == "PARSED"
        and campaign.stage == "EVALUATING"
        and campaign.last_filter is not None
    )


def render_verdict_summary(campaign: Campaign, *, skipped_locked: int = 0) -> str:
    """Short post-judgment chat: counts only, no creator-id lists."""
    verdicts = sort_verdicts(campaign.verdicts or [])
    model_name = campaign.verdict_model_name or "unknown"
    fit_ids = set(fit_creator_ids(campaign))
    pending = [v for v in verdicts if v.decision == "pending"]
    unfit = [v for v in verdicts if v.decision == "unfit"]
    n = len(fit_ids)
    target = target_count(campaign)
    mismatches = [v for v in unfit if v.topic_match == "mismatch"]
    audience_pending = [
        v
        for v in pending
        if v.rule_override == AUDIENCE_OVERRIDE or "audience" in (v.unknowns or [])
    ]
    parts: list[str] = []
    if target > 0:
        gap = max(target - n, 0)
        head = f"匹配判断完成 {LLM_LABEL} {model_name}。合格 {n}/{target}"
        if gap:
            head += f"，缺口 {gap}"
        parts.append(head + "。")
    else:
        parts.append(f"匹配判断完成 {LLM_LABEL} {model_name}。合格 {n}。")
    if mismatches:
        parts.append(f"主题不符 {len(mismatches)} 位未入名单。")
    if audience_pending:
        parts.append(f"受众未知 {len(audience_pending)} 位待确认未计入合格。")
    if target > 0 and n < target:
        parts.append(
            "下一步：接受当前短名单，或在表里点一位合适达人「生成草稿」；"
            "主题不符与受众未知不计入合格。"
        )
    elif fit_ids:
        parts.append("表里点「草稿」为该达人写一封。")
    skipped = skipped_locked_note(skipped_locked)
    if skipped:
        parts.append(skipped)
    locked = locked_rule_note(len(campaign.topic_rejected_ids))
    if locked:
        parts.append(locked)
    if campaign.verdict_rejected:
        parts.append(f"应用层拒绝了 {len(campaign.verdict_rejected)} 条判断。")
        topic_errors = [
            TopicRejected(creator_id=item.creator_id or "?", error_code=code)
            for item in campaign.verdict_rejected
            if (code := item.error_code) in ("topic_conflict", "quote_not_found")
        ]
        note = rejudge_note(topic_errors)
        if note:
            # Keep the note but without expanding into a long id roster when empty.
            parts.append(note)
    return "".join(parts)


def render_verdict_failure(error_code: str) -> str:
    if error_code == ModelUnavailable.code:
        return (
            f"匹配判断未完成：{error_code}。DeepSeek 不可用，没有生成任何候选名单；"
            "活动停在 EVALUATING，稍后再发一条消息即可重试。"
        )
    return (
        f"匹配判断未完成：{error_code}。模型两次输出的判断 JSON 未通过校验，"
        "未写入任何判断；再发一条消息即可重试。"
    )


class ApplicationService:
    def __init__(
        self,
        settings: AgentSettings,
        store: SQLiteSessionStore,
        providers: ProviderRegistry,
        runtime: AgentRuntime,
        context: ContextBuilder,
        goal_prompt_path: Path | None = None,
    ):
        self.settings = settings
        self.store = store
        self.campaigns = CampaignStore(store)
        self.providers = providers
        self.runtime = runtime
        self.context = context
        candidate = goal_prompt_path or settings.project_root / GOAL_PROMPT_RELATIVE
        self.goal_prompt_path = (
            candidate if candidate.exists() else PROJECT_ROOT / GOAL_PROMPT_RELATIVE
        )
        campaign_candidate = settings.project_root / CAMPAIGN_PROMPT_RELATIVE
        self.campaign_prompt_path = (
            campaign_candidate
            if campaign_candidate.exists()
            else PROJECT_ROOT / CAMPAIGN_PROMPT_RELATIVE
        )
        retry_candidate = settings.project_root / RETRY_PROMPT_RELATIVE
        self.retry_prompt_path = (
            retry_candidate if retry_candidate.exists() else PROJECT_ROOT / RETRY_PROMPT_RELATIVE
        )
        drafts_candidate = settings.project_root / DRAFTS_PROMPT_RELATIVE
        self.drafts_prompt_path = (
            drafts_candidate if drafts_candidate.exists() else PROJECT_ROOT / DRAFTS_PROMPT_RELATIVE
        )
        follow_candidate = settings.project_root / FOLLOW_UP_PROMPT_RELATIVE
        self.follow_up_prompt_path = (
            follow_candidate
            if follow_candidate.exists()
            else PROJECT_ROOT / FOLLOW_UP_PROMPT_RELATIVE
        )

    def history(self, session_id: UUID) -> list[Message]:
        return self.store.list_messages(session_id)

    def history_entries(self, session_id: UUID) -> list[StoredMessage]:
        return self.store.list_history(session_id)

    def list_projects(self) -> list[ProjectSummary]:
        return self.store.list_projects()

    def create_project(self, title: str | None = None) -> ProjectSummary:
        session_id = self.store.create_session(title=title)
        project = self.store.get_project(session_id)
        assert project is not None
        return project

    def rename_project(self, session_id: UUID, title: str) -> ProjectSummary | None:
        """Persist a new display name. Returns None when the title is empty."""
        if not self.store.set_title(session_id, title):
            return None
        return self.store.get_project(session_id)

    def delete_project(self, session_id: UUID) -> None:
        self.campaigns.delete_for_session(session_id)
        self.store.delete_session_rows(session_id)

    def delete_turn(self, session_id: UUID, turn_id: UUID) -> int:
        return self.store.delete_turn(session_id, turn_id)

    def delete_message(self, session_id: UUID, message_id: UUID) -> int:
        return self.store.delete_message(session_id, message_id)

    # ------------------------------------------------------------------
    # Campaign record (stored in session metadata until T09)
    # ------------------------------------------------------------------

    def campaign(self, session_id: UUID) -> Campaign:
        return self.campaigns.get(session_id)

    def get_workbench_state(self, campaign_id: UUID | None) -> WorkbenchState:
        """Read-only page snapshot. Does not write the campaign store."""
        if campaign_id is None:
            return build_workbench_state(None)
        return build_workbench_state(self.campaigns.get(campaign_id))

    def save_campaign(self, campaign: Campaign) -> None:
        self.campaigns.save(campaign)

    def queue_save_selection(self, session_id: UUID, creator_ids: list[str]) -> Campaign:
        updated = queue_save_selection(self.campaign(session_id), creator_ids)
        self.save_campaign(updated)
        return updated

    def queue_exclude_creator(self, session_id: UUID, creator_id: str) -> Campaign:
        updated = queue_exclude_creator(self.campaign(session_id), creator_id)
        self.save_campaign(updated)
        return updated

    def queue_confirm_channel(
        self, session_id: UUID, creator_id: str, channel: str
    ) -> Campaign:
        updated = queue_confirm_channel(self.campaign(session_id), creator_id, channel)
        self.save_campaign(updated)
        return updated

    def review_draft(
        self, session_id: UUID, draft_id: str, approved: bool
    ) -> tuple[Campaign, str]:
        campaign = self.campaign(session_id)
        if approved:
            updated, display = apply_approve_draft(campaign, draft_id)
        else:
            updated, display = apply_reject_draft(campaign, draft_id)
        self.save_campaign(updated)
        return updated, display

    def note_follow_up(
        self, session_id: UUID, follow_up_id: str, user_approved: bool
    ) -> tuple[Campaign, str]:
        campaign = self.campaign(session_id)
        if not user_approved:
            return campaign, "记下跟进需要你确认，状态未改。"
        updated, display = apply_note_follow_up(campaign, follow_up_id)
        self.save_campaign(updated)
        return updated, display

    async def review_draft_and_follow_up(
        self, session_id: UUID, draft_id: str, approved: bool
    ) -> tuple[Campaign, str]:
        updated, display = self.review_draft(session_id, draft_id, approved)
        if not approved:
            return updated, display
        updated, batch = await self.generate_and_queue_follow_up(session_id, draft_id)
        if batch.ok:
            return updated, f"{display} 已生成跟进事项，等你记录。"
        if batch.error_code:
            return updated, f"{display} 跟进未写入：{batch.error_code}。"
        return updated, display

    def approve_pending(
        self, campaign_id: UUID, decision: str, user_approved: bool
    ) -> DecisionResult:
        result = approve_pending(self.campaign(campaign_id), decision, user_approved)
        if result.ok:
            self.save_campaign(result.campaign)
        return result

    def goal_prompt(self, campaign: Campaign) -> str:
        template = self.goal_prompt_path.read_text(encoding="utf-8")
        parsed = (
            json.dumps(campaign.parsed_goal.model_dump(), ensure_ascii=False, indent=2)
            if campaign.parsed_goal
            else "null"
        )
        return (
            template.replace("{goal_status}", campaign.goal_status)
            .replace("{grill_rounds}", str(campaign.grill_rounds))
            .replace("{pending_decision}", campaign.pending_decision or "无")
            .replace("{parsed_goal}", parsed)
        )

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    async def chat(
        self,
        content: str,
        session_id: UUID | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        on_delta: Callable[[str], Awaitable[None]] | None = None,
        on_event: EventHandler | None = None,
        creative: bool = False,
        creator_ids: list[str] | None = None,
    ) -> ChatResult:
        provider_name = provider_name or self.settings.model.default_provider
        model = model or self.settings.model.default_model
        session_id = self.store.ensure_session(session_id)
        turn_id = uuid4()
        logger = get_logger(session_id=str(session_id), turn_id=str(turn_id))
        logger.info("turn.started")

        campaign = self.campaign(session_id)
        user_message = Message(role="user", content=content)
        self.store.add_message(session_id, turn_id, user_message)
        self.store.maybe_set_title_from_prompt(session_id, content)

        # Chat「生成草稿」never batch-writes. Point the user at the per-row table action.
        if is_generate_drafts_request(content):
            display: str
            if campaign.pending_decision == SAVE_DRAFTS:
                result = self.approve_pending(session_id, SAVE_DRAFTS, True)
                display = result.display
                updated = result.campaign
            elif campaign.drafts:
                display = (
                    "草稿已在右侧「草稿」区展示（创作者、渠道、引用与正文）。"
                    "可用「查看草稿」打开；若要再写一位，请在表里选合适达人后点「生成草稿」。"
                    "草稿不会发送。"
                )
                updated = campaign
            else:
                display = PICK_CREATOR_FOR_DRAFT
                updated = campaign
            self.store.add_message(
                session_id, turn_id, Message(role="assistant", content=display)
            )
            logger.info("turn.completed", drafts_shortcut=True)
            return ChatResult(
                session_id=session_id,
                turn_id=turn_id,
                content=display,
                provider=provider_name,
                model=model,
                goal_status=updated.goal_status,
                pending_decision=updated.pending_decision,
            )

        # 「确认」in chat equals approving the single pending decision.
        if campaign.pending_decision and is_confirmation(content):
            result = self.approve_pending(session_id, campaign.pending_decision, True)
            self.store.add_message(
                session_id, turn_id, Message(role="assistant", content=result.display)
            )
            logger.info("turn.completed", decision=result.decision, status=result.status)
            return ChatResult(
                session_id=session_id,
                turn_id=turn_id,
                content=result.display,
                provider=provider_name,
                model=model,
                goal_status=result.campaign.goal_status,
                pending_decision=result.campaign.pending_decision,
            )

        provider = self.providers.get(provider_name)

        # Stored tool messages lack the assistant tool_calls they answer, so
        # providers would reject them as orphans.
        history = [
            message
            for message in self.store.list_messages(session_id)
            if message.role != "tool"
        ]
        messages = self.context.build(history)
        messages[0].content = f"{messages[0].content}\n\n{self.goal_prompt(campaign)}"
        temperature = (
            self.settings.model.creative_temperature if creative else None
        )
        run_kwargs: dict[str, Any] = {
            "provider": provider,
            "model": model,
            "session_id": session_id,
            "turn_id": turn_id,
            "on_delta": on_delta,
            "on_event": on_event,
            "temperature": temperature,
            "disabled_tools": (
                frozenset() if campaign.goal_status == "PARSED" else SEARCH_TOOLS
            ),
        }

        try:
            response, generated, tool_call_count = await self.runtime.run(
                messages=messages, **run_kwargs
            )
            # Campaign tools (search, filter) write the record while running.
            campaign = self.campaign(session_id)
            campaign, reply, retry_generated, retry_calls = await self._resolve_goal(
                campaign, response, messages, run_kwargs
            )
            generated += retry_generated
            tool_call_count += retry_calls
            if needs_evaluation(campaign):
                campaign, summary = await self._evaluate_candidates(
                    campaign, provider, model, session_id, turn_id, on_event
                )
                extra = ""
                if campaign.verdicts is not None:
                    campaign, extra = await self._maybe_search_retry(
                        campaign, provider, model, session_id, turn_id, on_event
                    )
                # Judgment reply is the short application summary only — drop
                # long tool/LLM filler that listed every creator or how-to-勾选.
                reply = "\n\n".join(part for part in (summary, extra) if part).strip()
            for message in generated:
                self.store.add_message(session_id, turn_id, message)
            assistant = Message(role="assistant", content=reply)
            self.store.add_message(session_id, turn_id, assistant)
            self.save_campaign(campaign)
            logger.info(
                "turn.completed",
                provider=response.provider,
                model=response.model,
                goal_status=campaign.goal_status,
            )
            return ChatResult(
                session_id=session_id,
                turn_id=turn_id,
                content=assistant.content,
                provider=response.provider,
                model=response.model,
                tool_calls=tool_call_count,
                goal_status=campaign.goal_status,
                pending_decision=campaign.pending_decision,
            )
        except Exception as exc:
            logger.error(
                "turn.failed",
                error_code=getattr(exc, "code", "unexpected_error"),
                error_type=type(exc).__name__,
            )
            raise

    # ------------------------------------------------------------------
    # Judgment step (T05): one dedicated model call, validated by verdict.py
    # ------------------------------------------------------------------

    def campaign_prompt(self, campaign: Campaign, window_days: int) -> str:
        goal = campaign.parsed_goal
        assert goal is not None
        return render_campaign_prompt(
            self.campaign_prompt_path.read_text(encoding="utf-8"),
            brand=mock_store.load_brand(),
            goal_brand=goal.brand,
            goal_product=goal.product,
            target_audience=goal.target_audience,
            inclusion_criteria=goal.inclusion_criteria,
            exclusion_criteria=goal.exclusion_criteria,
            target_count=goal.target_count,
            window_days=window_days,
        )

    async def evaluate_candidates(
        self, campaign: Campaign, provider: Provider, model: str
    ) -> tuple[VerdictBatch, str, int]:
        """Ask the model for Verdict[] over `last_filter.kept`, validate, retry
        the whole batch once. Raises ModelUnavailable; never ranks by itself.
        Locked mismatch / own-brand ids are subtracted before the call."""
        assert campaign.last_filter is not None and campaign.last_search is not None
        creators = mock_store.load()
        excluded = ids_excluded_from_judgment(campaign)
        skipped_locked = sum(
            1 for creator_id in campaign.last_filter.kept_ids if creator_id in campaign.topic_rejected_ids
        )
        candidates = {
            creator_id: creators[creator_id]
            for creator_id in campaign.last_filter.kept_ids
            if creator_id in creators and creator_id not in excluded
        }
        window_days = campaign.last_search.window_days
        if not candidates:
            return VerdictBatch(accepted=[]), model, skipped_locked
        messages = [
            Message(role="system", content=self.campaign_prompt(campaign, window_days)),
            Message(role="user", content=render_candidates_message(list(candidates.values()))),
        ]
        batch = VerdictBatch(accepted=[], error_code="verdicts_invalid")
        model_name = model
        for attempt in range(2):
            try:
                response = await provider.complete(messages, model, tools=[])
            except (ProviderError, MissingApiKeyError) as exc:
                raise ModelUnavailable("Judgment model call failed") from exc
            model_name = response.model
            text = response.content or ""
            block = extract_json_block(text)
            batch = validate_verdicts(
                block.data if block else None,
                candidates,
                window_days=window_days,
                model_name=model_name,
            )
            if batch.ok:
                topic = validate_topic_verdicts(batch.accepted, candidates)
                accepted = apply_audience_overrides(topic.accepted, candidates)
                batch = VerdictBatch(
                    accepted=accepted,
                    rejected=[
                        *batch.rejected,
                        *[
                            RejectedVerdict(
                                creator_id=item.creator_id,
                                error_code=item.error_code,
                                detail=item.detail,
                            )
                            for item in topic.rejected
                        ],
                    ],
                )
                break
            if attempt == 1:
                break
            messages += [
                Message(role="assistant", content=text),
                Message(
                    role="user",
                    content=(
                        f"上一条判断 JSON 未通过校验（{batch.error_code}）。"
                        "fit 的 rank 必须从 1 开始连续且不重复，unfit/pending 的 rank 必须为 null，"
                        "每条必须引用该候选人自己的 evidence id。"
                        "topic_match=mismatch 时 decision 必须为 unfit，并给出原文 quote。"
                        "请只重新输出修正后的 ```json 代码块。"
                    ),
                ),
            ]
        return batch, model_name, skipped_locked

    async def _evaluate_candidates(
        self,
        campaign: Campaign,
        provider: Provider,
        model: str,
        session_id: UUID,
        turn_id: UUID,
        on_event: EventHandler | None,
    ) -> tuple[Campaign, str]:
        logger = get_logger(session_id=str(session_id), turn_id=str(turn_id))

        async def emit(ok: bool | None, error_code: str | None = None) -> None:
            if on_event:
                await on_event(
                    RuntimeEvent(
                        type="tool.started" if ok is None else "tool.completed",
                        session_id=session_id,
                        turn_id=turn_id,
                        name=EVALUATE_STEP,
                        ok=ok,
                        error_code=error_code,
                    )
                )

        await emit(None)
        try:
            batch, model_name, skipped_locked = await self.evaluate_candidates(
                campaign, provider, model
            )
        except ModelUnavailable as exc:
            logger.warning("evaluate.failed", error_code=exc.code)
            await emit(False, exc.code)
            updated = campaign.model_copy(update={"verdict_error": exc.code})
            return updated, render_verdict_failure(exc.code)
        if not batch.ok:
            logger.warning("evaluate.invalid", error_code=batch.error_code)
            await emit(False, batch.error_code)
            updated = campaign.model_copy(
                update={"verdict_error": batch.error_code, "verdict_rejected": batch.rejected}
            )
            return updated, render_verdict_failure(batch.error_code or "verdicts_invalid")
        await emit(True)
        kept_ids = (
            campaign.last_filter.kept_ids if campaign.last_filter is not None else []
        )
        merged = retain_prior_fits(campaign.verdicts, batch.accepted, kept_ids)
        updated = campaign.model_copy(
            update={
                "verdicts": sort_verdicts(merged),
                "verdict_rejected": batch.rejected,
                "verdict_model_name": model_name,
                "verdict_error": None,
            }
        )
        updated = lock_topic_rejections(updated, batch.accepted)
        updated = append_search_round(
            updated, strategy=campaign.retry_strategy if campaign.auto_retries else None
        )
        updated = refresh_accept_short_list(updated)
        logger.info(
            "evaluate.completed",
            model=model_name,
            accepted=len(batch.accepted),
            retained=len(merged),
            rejected=len(batch.rejected),
            locked=len(updated.topic_rejected_ids),
        )
        return updated, render_verdict_summary(updated, skipped_locked=skipped_locked)

    def retry_prompt(self) -> str:
        return self.retry_prompt_path.read_text(encoding="utf-8")

    def drafts_prompt(self, campaign: Campaign) -> str:
        goal = campaign.parsed_goal
        return render_drafts_prompt(
            self.drafts_prompt_path.read_text(encoding="utf-8"),
            brand=(goal.brand if goal and goal.brand else "未指定品牌"),
            product=(goal.product if goal and goal.product else "未指定产品"),
        )

    async def generate_drafts(
        self,
        campaign: Campaign,
        provider: Provider,
        model: str,
        creator_ids: list[str] | None = None,
    ) -> DraftBatch:
        """Ask the model for one draft per selected creator that has a channel.

        Creators with no usable channel get a placeholder card. Does not call
        the model when the selection is empty.
        """
        targets = outreach_ids(campaign, creator_ids)
        error = draft_prerequisites(campaign, targets)
        if error:
            return DraftBatch(error_code=error, model_called=False, expected_count=0)
        creators = mock_store.load()
        channels = resolve_channels(targets, creators)
        payload = drafts_payload(campaign, creators, targets, channels)
        if not payload:
            # Every selected creator lacks a channel — still return cards.
            from collabpilot.campaign.drafts import placeholder_draft

            accepted = [
                placeholder_draft(campaign, creator_id, model_name=model)
                for creator_id in targets
            ]
            return DraftBatch(
                accepted=accepted,
                model_called=False,
                model_name=model,
                expected_count=len(targets),
            )
        messages = [
            Message(role="system", content=self.drafts_prompt(campaign)),
            Message(role="user", content=render_drafts_message(payload)),
        ]
        batch = DraftBatch(
            error_code="drafts_invalid",
            model_called=True,
            expected_count=len(targets),
        )
        for attempt in range(2):
            try:
                response = await provider.complete(
                    messages,
                    model,
                    tools=[],
                    temperature=self.settings.model.creative_temperature,
                )
            except (ProviderError, MissingApiKeyError):
                return DraftBatch(
                    error_code=ModelUnavailable.code,
                    model_called=True,
                    expected_count=len(targets),
                )
            text = response.content or ""
            block = extract_json_block(text)
            batch = validate_drafts(
                block.data if block else None,
                campaign,
                creators,
                model_name=response.model,
                creator_ids=targets,
                channels=channels,
            )
            batch.model_called = True
            if batch.ok:
                break
            if attempt == 1:
                break
            messages += [
                Message(role="assistant", content=text),
                Message(
                    role="user",
                    content=(
                        f"上一条草稿 JSON 未通过校验（{batch.error_code}）。"
                        f"共 {len(payload)} 封 body 与 cited_post_id 必须互异，"
                        "cited_post_id 必须属于该创作者，"
                        "body 必须含渠道中文名以及所引帖子不少于 8 字的原文。"
                        "请只重新输出修正后的 ```json 代码块。"
                    ),
                ),
            ]
        return batch

    async def generate_and_queue_drafts(
        self,
        session_id: UUID,
        provider_name: str | None = None,
        model: str | None = None,
        creator_ids: list[str] | None = None,
    ) -> tuple[Campaign, DraftBatch]:
        campaign = self.campaign(session_id)
        provider_name = provider_name or self.settings.model.default_provider
        model = model or self.settings.model.default_model
        provider = self.providers.get(provider_name)
        targets = outreach_ids(campaign, creator_ids)
        batch = await self.generate_drafts(
            campaign, provider, model, creator_ids=targets
        )
        if not batch.ok:
            updated = campaign.model_copy(update={"draft_error": batch.error_code})
            self.save_campaign(updated)
            return updated, batch
        # Persist auto-picked channels so follow-up can reuse them without a
        # separate confirm-channel click.
        creators = mock_store.load()
        confirmed = dict(campaign.confirmed_channels)
        for draft in batch.accepted:
            if draft.channel:
                confirmed[draft.creator_id] = draft.channel
            else:
                auto = pick_channel(creators.get(draft.creator_id))
                if auto:
                    confirmed[draft.creator_id] = auto
        campaign = campaign.model_copy(update={"confirmed_channels": confirmed})
        queued = queue_save_drafts(campaign, batch.accepted)
        self.save_campaign(queued)
        return queued, batch

    def follow_up_prompt(self, campaign: Campaign) -> str:
        goal = campaign.parsed_goal
        return render_follow_up_prompt(
            self.follow_up_prompt_path.read_text(encoding="utf-8"),
            brand=(goal.brand if goal and goal.brand else "未指定品牌"),
        )

    async def generate_follow_up(
        self, campaign: Campaign, provider: Provider, model: str, draft_id: str
    ) -> FollowUpBatch:
        """Ask the model for one follow-up. Does not call the model when the
        draft is not approved or a follow-up already exists."""
        error = follow_up_prerequisites(campaign, draft_id)
        if error:
            return FollowUpBatch(error_code=error, model_called=False)
        payload = follow_up_payload(campaign, draft_id)
        if payload is None:
            return FollowUpBatch(error_code="channel_mismatch", model_called=False)
        messages = [
            Message(role="system", content=self.follow_up_prompt(campaign)),
            Message(role="user", content=render_follow_up_message(payload)),
        ]
        batch = FollowUpBatch(error_code="follow_up_invalid", model_called=True)
        for attempt in range(2):
            try:
                response = await provider.complete(
                    messages,
                    model,
                    tools=[],
                    temperature=self.settings.model.creative_temperature,
                )
            except (ProviderError, MissingApiKeyError):
                return FollowUpBatch(
                    error_code=ModelUnavailable.code, model_called=True
                )
            text = response.content or ""
            block = extract_json_block(text)
            batch = validate_follow_up(
                block.data if block else None,
                campaign,
                draft_id=draft_id,
                model_name=response.model,
            )
            batch.model_called = True
            if batch.ok:
                break
            if attempt == 1:
                break
            messages += [
                Message(role="assistant", content=text),
                Message(
                    role="user",
                    content=(
                        f"上一条跟进 JSON 未通过校验（{batch.error_code}）。"
                        "channel 必须等于已确认渠道，next_step 必须非空，"
                        "creator_id 与 draft_id 必须与材料一致。"
                        "请只重新输出修正后的 ```json 代码块。"
                    ),
                ),
            ]
        return batch

    async def generate_and_queue_follow_up(
        self, session_id: UUID, draft_id: str
    ) -> tuple[Campaign, FollowUpBatch]:
        campaign = self.campaign(session_id)
        provider = self.providers.get(self.settings.model.default_provider)
        model = self.settings.model.default_model
        batch = await self.generate_follow_up(campaign, provider, model, draft_id)
        if not batch.ok:
            updated = campaign.model_copy(update={"follow_error": batch.error_code})
            self.save_campaign(updated)
            return updated, batch
        queued = queue_save_follow_up(campaign, batch.accepted)
        self.save_campaign(queued)
        return queued, batch


    async def request_retry_strategy(
        self, campaign: Campaign, provider: Provider, model: str
    ) -> StrategyOutcome:
        summary = build_round_summary(campaign)
        messages = [
            Message(role="system", content=self.retry_prompt()),
            Message(role="user", content=render_retry_message(summary)),
        ]
        round1 = summary.round
        try:
            response = await provider.complete(messages, model, tools=[])
        except (ProviderError, MissingApiKeyError):
            return StrategyOutcome(error_code=MODEL_STRATEGY_REQUIRED, detail="model_unavailable")
        block = extract_json_block(response.content or "")
        parsed = parse_retry_strategy(block.data if block else None, response.model)
        if parsed.strategy is None:
            return parsed
        return accept_retry_strategy(round1, parsed.strategy)

    async def _maybe_search_retry(
        self,
        campaign: Campaign,
        provider: Provider,
        model: str,
        session_id: UUID,
        turn_id: UUID,
        on_event: EventHandler | None,
    ) -> tuple[Campaign, str]:
        if not is_insufficient(campaign):
            updated = campaign.model_copy(update={"stage": "CANDIDATES_READY", "retry_error": None})
            return updated, ""
        # 合格 n/target already stated in render_verdict_summary; only append next step.
        n = fit_count(campaign)
        target = target_count(campaign)
        lines: list[str] = []
        if campaign.auto_retries >= MAX_AUTO_RETRIES:
            updated = queue_accept_short_list(campaign)
            if campaign.auto_retries == 0:
                lines.append(
                    f"合格 {n}/{target}，人数不足。"
                    "是否接受当前短名单，或在表里点一位合适达人「生成草稿」？"
                    "不会把主题不符或受众未知改成合适。"
                )
            else:
                lines.append(
                    f"第二轮仍不足（合格 {n}/{target}）。是否接受当前人数？"
                    "在你决定之前不会写邀请草稿；不会把不合适或待确认的人改成合适。"
                )
            return updated, "\n".join(lines)
        insufficient = campaign.model_copy(update={"stage": "INSUFFICIENT"})
        self.save_campaign(insufficient)

        async def emit_retry(ok: bool | None, error_code: str | None = None) -> None:
            if on_event:
                await on_event(
                    RuntimeEvent(
                        type="tool.started" if ok is None else "tool.completed",
                        session_id=session_id,
                        turn_id=turn_id,
                        name=RETRY_STEP,
                        ok=ok,
                        error_code=error_code,
                    )
                )

        await emit_retry(None)
        outcome = await self.request_retry_strategy(insufficient, provider, model)
        await emit_retry(outcome.ok, None if outcome.ok else outcome.error_code)
        if not outcome.ok or outcome.params is None or outcome.strategy is None:
            error = outcome.error_code or MODEL_STRATEGY_REQUIRED
            updated = insufficient.model_copy(update={"retry_error": error})
            window = (
                updated.last_search.window_days if updated.last_search is not None else None
            )
            lines.append(render_strategy_failure(error))
            if window is not None:
                lines.append(f"当前窗口仍为 {window} 天。")
            return updated, "\n".join(lines)
        retrying = insufficient.model_copy(
            update={
                "stage": "RETRYING",
                "retry_strategy": outcome.strategy,
                "auto_retries": insufficient.auto_retries + 1,
                "retry_error": None,
            }
        )
        self.save_campaign(retrying)
        context = ToolContext(session_id=session_id, turn_id=turn_id)

        async def emit(name: str, ok: bool | None, error_code: str | None = None) -> None:
            if on_event:
                await on_event(
                    RuntimeEvent(
                        type="tool.started" if ok is None else "tool.completed",
                        session_id=session_id,
                        turn_id=turn_id,
                        name=name,
                        ok=ok,
                        error_code=error_code,
                    )
                )

        await emit(SearchCreatorsTool.name, None)
        search = await SearchCreatorsTool(self.campaigns).execute(outcome.params, context)
        await emit(SearchCreatorsTool.name, search.ok, search.error_code)
        if not search.ok:
            return retrying, "\n".join([*lines, render_strategy_reply(outcome.strategy), search.display])
        await emit(ApplyHardFiltersTool.name, None)
        filtered = await ApplyHardFiltersTool(self.campaigns).execute({}, context)
        await emit(ApplyHardFiltersTool.name, filtered.ok, filtered.error_code)
        campaign = self.campaign(session_id)
        campaign = campaign.model_copy(
            update={
                "retry_strategy": outcome.strategy,
                "auto_retries": retrying.auto_retries,
                "stage": campaign.stage,
            }
        )
        self.save_campaign(campaign)
        campaign, eval_summary = await self._evaluate_candidates(
            campaign, provider, model, session_id, turn_id, on_event
        )
        more = ""
        if campaign.verdicts is not None:
            campaign, more = await self._maybe_search_retry(
                campaign, provider, model, session_id, turn_id, on_event
            )
        return campaign, "\n".join(
            [
                *lines,
                render_strategy_reply(outcome.strategy),
                search.display,
                filtered.display,
                eval_summary,
                more,
            ]
        ).strip()

    async def _resolve_goal(
        self,
        campaign: Campaign,
        response: ModelResponse,
        messages: list[Message],
        run_kwargs: dict[str, Any],
    ) -> tuple[Campaign, str, list[Message], int]:
        """Extract + validate the goal JSON. Returns the campaign to persist,
        the reply text, and any extra tool messages / tool-call count from the
        single validation retry."""
        text = response.content or ""
        block = extract_json_block(text)
        if block is None:
            return campaign, text, [], 0

        outcome = validate_parsed_goal(block.data)
        retry_generated: list[Message] = []
        retry_calls = 0
        if isinstance(outcome, list):
            # One correction round, then give up for this turn.
            correction = Message(
                role="user",
                content=(
                    f"上一条回复里的目标 JSON 未通过校验，字段：{', '.join(outcome)}。"
                    "请只重新输出一个修正后的 ```json 代码块，键不可缺省。"
                ),
            )
            retry_messages = [
                *messages,
                Message(role="assistant", content=text),
                correction,
            ]
            response, retry_generated, retry_calls = await self.runtime.run(
                messages=retry_messages, **run_kwargs
            )
            text = response.content or ""
            block = extract_json_block(text)
            outcome = (
                validate_parsed_goal(block.data) if block else sorted(REQUIRED_KEYS)
            )
            if isinstance(outcome, list):
                reply = render_invalid_reply(strip_json_blocks(text), outcome)
                if campaign.goal_status == "PARSED":
                    return campaign, reply, retry_generated, retry_calls
                rounds = min(campaign.grill_rounds + 1, MAX_GRILL_ROUNDS)
                updated = campaign.model_copy(
                    update={
                        "goal_status": "CLARIFYING",
                        "grill_rounds": rounds,
                        "pending_decision": (
                            CONFIRM_ASSUMPTIONS
                            if rounds >= MAX_GRILL_ROUNDS
                            else campaign.pending_decision
                        ),
                    }
                )
                return updated, reply, retry_generated, retry_calls

        goal: ParsedGoal = outcome
        user_turns = [message.content for message in messages if message.role == "user"]
        user_text = user_turns[-1] if user_turns else ""
        goal = apply_user_cooperated_preference(goal, user_text or "")
        goal = ground_goal_in_user_text(goal, "\n".join(user_turns))
        prose = strip_json_blocks(text)
        base = {
            "parsed_goal": goal,
            "goal_origin": GOAL_ORIGIN,
            "goal_model_name": response.model,
        }
        if goal.missing_critical:
            rounds = min(campaign.grill_rounds + 1, MAX_GRILL_ROUNDS)
            confirm = rounds >= MAX_GRILL_ROUNDS
            grill_data = block.data.get("grill") if block and block.data else None
            grill = build_grill(goal, validate_grill(grill_data, goal))
            reply = render_clarifying_reply(prose, goal, grill, ask_confirmation=confirm)
            updated = campaign.model_copy(
                update={
                    **base,
                    "goal_status": "CLARIFYING",
                    "grill_rounds": rounds,
                    "pending_decision": (
                        CONFIRM_ASSUMPTIONS if confirm else campaign.pending_decision
                    ),
                }
            )
            return updated, reply, retry_generated, retry_calls

        reply = render_parsed_reply(prose, goal, response.model)
        fingerprint = fingerprint_goal(goal)
        same_task = (
            campaign.goal_fingerprint is not None
            and campaign.goal_fingerprint == fingerprint
        )
        updated = campaign.model_copy(
            update={
                **base,
                "goal_status": "PARSED",
                "goal_fingerprint": fingerprint if not same_task else campaign.goal_fingerprint,
                "pending_decision": (
                    None
                    if campaign.pending_decision == CONFIRM_ASSUMPTIONS
                    else campaign.pending_decision
                ),
            }
        )
        return updated, reply, retry_generated, retry_calls
