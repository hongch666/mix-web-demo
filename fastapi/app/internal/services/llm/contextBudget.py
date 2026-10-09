import math
from dataclasses import dataclass
from typing import Any

from app.core.constants import Defaults

# 历史对话的一轮记录，格式为 (用户提问, AI 回复)
ChatHistoryItem = tuple[str, str]


@dataclass(frozen=True)
class ContextBudgetConfig:
    """聊天上下文预算配置

    历史预算不单独配置，由模型窗口扣除系统提示词、用户提示词与各项预留后推导；
    字段默认值只覆盖「配置缺失或非法」的情况，生产取值以 application.yaml 的
    agent.closeai 段为准（冒号后的默认值即部署兜底），两处调整需保持同步
    """

    window_tokens: int = 32768
    output_reserve_tokens: int = 2048
    tool_reserve_tokens: int = 4000
    compact_trigger_ratio: float = 0.8
    keep_rounds: int = 4
    candidate_rounds: int = 40
    safety_ratio: float = 1.2
    single_message_chars: int = 2000
    summary_max_chars: int = 1200
    compact_input_chars: int = 12000

    @classmethod
    def from_agent_config(cls, service_cfg: dict[str, Any]) -> "ContextBudgetConfig":
        """从 agent 配置构建预算，缺失或非法时回退到字段默认值"""
        defaults = cls()
        keep_rounds = _positive_int(
            service_cfg.get("context_keep_rounds"),
            defaults.keep_rounds,
        )
        candidate_rounds = _positive_int(
            service_cfg.get("context_candidate_rounds"),
            defaults.candidate_rounds,
        )
        return cls(
            window_tokens=_positive_int(
                service_cfg.get("context_window_tokens"),
                defaults.window_tokens,
            ),
            output_reserve_tokens=_positive_int(
                service_cfg.get("context_output_reserve_tokens"),
                defaults.output_reserve_tokens,
            ),
            tool_reserve_tokens=_positive_int(
                service_cfg.get("context_tool_reserve_tokens"),
                defaults.tool_reserve_tokens,
            ),
            compact_trigger_ratio=_ratio(
                service_cfg.get("context_compact_trigger_ratio"),
                defaults.compact_trigger_ratio,
            ),
            keep_rounds=keep_rounds,
            # 候选轮数必须不小于保留轮数，否则保留窗口取不到足够的历史
            candidate_rounds=max(candidate_rounds, keep_rounds),
            safety_ratio=_positive_float(
                service_cfg.get("context_safety_ratio"),
                defaults.safety_ratio,
            ),
            single_message_chars=_positive_int(
                service_cfg.get("context_single_message_chars"),
                defaults.single_message_chars,
            ),
            summary_max_chars=_positive_int(
                service_cfg.get("context_summary_max_chars"),
                defaults.summary_max_chars,
            ),
            compact_input_chars=_positive_int(
                service_cfg.get("context_compact_input_chars"),
                defaults.compact_input_chars,
            ),
        )

    def reserved_tokens(self, prompt_tokens: int, use_tools: bool = False) -> int:
        """提示词与各项预留占用的 token 总量

        Args:
            prompt_tokens: 系统提示词与用户提示词的估算 token 数
            use_tools: 是否走带工具的 Agent 路径，该路径需要额外的工具预留

        Returns:
            int: 提示词、输出预留与工具预留的估算 token 合计
        """
        reserved = prompt_tokens + self.output_reserve_tokens
        if use_tools:
            reserved += self.tool_reserve_tokens
        return reserved

    def history_budget(self, prompt_tokens: int, use_tools: bool = False) -> int:
        """按模型窗口扣除提示词与预留，得到历史可用的 token 预算

        返回的是原始估算预算，安全系数只在比较处由 _budgeted_tokens 放大一次，
        避免预算与判断两侧同时折算导致实际可用额度被压缩两次；
        窗口被提示词与预留占满时返回 0，表示本轮不能再注入历史

        Args:
            prompt_tokens: 系统提示词与用户提示词的估算 token 数
            use_tools: 是否走带工具的 Agent 路径，该路径需要额外的工具预留

        Returns:
            int: 历史可用的估算 token 预算，窗口不足时为 0
        """
        # 负预算按 0 返回，交由调用方决定降级方式
        return max(
            self.window_tokens - self.reserved_tokens(prompt_tokens, use_tools), 0
        )


@dataclass(frozen=True)
class ContextTrimResult:
    """上下文裁剪结果"""

    history: list[ChatHistoryItem]
    estimated_tokens: int
    dropped_rounds: int
    truncated: bool


@dataclass(frozen=True)
class ContextPlan:
    """单次请求的上下文组装方案"""

    # 已持久化的历史摘要，未触发压缩时原样沿用
    summary: str
    # 实际注入提示词的原文轮次
    history: list[ChatHistoryItem]
    # 需要折叠进摘要的更早轮次，为空表示不需要压缩
    compact_targets: list[ChatHistoryItem]
    # 按窗口推导出的历史预算
    budget_tokens: int
    # 摘要与注入历史合计的保守估算 token 数
    estimated_tokens: int

    @property
    def should_compact(self) -> bool:
        return bool(self.compact_targets)


@dataclass(frozen=True)
class CompactBatch:
    """单次记忆压缩的输入批次"""

    # 已按字符上限收敛的折叠内容，按旧到新排列
    rounds: list[ChatHistoryItem]
    # 批次中最后一条历史记录的 id，压缩成功后作为新水位线
    last_id: int
    # 本批次折叠的轮数
    count: int


def plan_compact_batch(
    items: list[tuple[int, str, str]], config: ContextBudgetConfig
) -> CompactBatch:
    """从待折叠记录中取出单次压缩可容纳的最长前缀

    折叠内容会连同既有摘要一起进入模型，因此单条按 single_message_chars 收敛、
    整体按 compact_input_chars 收敛，避免压缩请求自身超出模型窗口而必然失败；
    未纳入批次的记录保留在原表中，下一轮仍在水位线之后，可继续折叠

    Args:
        items: 待折叠记录，元素为 (历史记录 id, 提问, 回复)，按旧到新排列
        config: 上下文预算配置

    Returns:
        CompactBatch: 折叠内容、新水位线与折叠轮数，无可折叠内容时 rounds 为空
    """
    rounds: list[ChatHistoryItem] = []
    used_chars = 0
    last_id = 0
    for history_id, ask, reply in items:
        normalized = _truncate_round((ask, reply), config.single_message_chars)
        round_chars = len(normalized[0]) + len(normalized[1])
        # 至少折叠一轮，避免输入上限小于单轮长度时压缩永远无法推进
        if rounds and used_chars + round_chars > config.compact_input_chars:
            break
        rounds.append(normalized)
        used_chars += round_chars
        last_id = history_id

    return CompactBatch(rounds=rounds, last_id=last_id, count=len(rounds))


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数

    三个模型的分词器与 OpenAI 并不一致，这里按字符类别做保守估算，
    仅用于上下文预算判断，不作为计费依据
    """
    if not text:
        return 0
    cjk_chars = sum(1 for char in text if _is_cjk(char))
    other_chars = len(text) - cjk_chars
    return cjk_chars + math.ceil(
        other_chars / Defaults.CHAT_CONTEXT_NON_CJK_CHARS_PER_TOKEN
    )


def plan_chat_context(
    summary: str,
    history: list[ChatHistoryItem],
    config: ContextBudgetConfig,
    prompt_tokens: int,
    use_tools: bool = False,
) -> ContextPlan:
    """规划上下文注入范围与 compact 压缩范围

    历史未超过预算且未接近触发阈值时按原样注入；
    超出预算或占用达到触发比例时，把注入窗口之外的更早轮次折叠进摘要

    Args:
        summary: 已持久化的用户级历史摘要
        history: 水位线之后的原文轮次，按旧到新排列，长度不应超过候选轮数
        config: 上下文预算配置
        prompt_tokens: 系统提示词与用户提示词的估算 token 数
        use_tools: 是否走带工具的 Agent 路径

    Returns:
        ContextPlan: 摘要、注入轮次、待压缩轮次与预算信息
    """
    summary_text = summary.strip()
    summary_tokens = _summary_tokens(summary_text)
    budget_tokens = config.history_budget(prompt_tokens, use_tools)
    if budget_tokens <= 0:
        # 窗口已被提示词与预留占满，本轮不注入摘要与历史，也不触发压缩
        return ContextPlan(
            summary="",
            history=[],
            compact_targets=[],
            budget_tokens=0,
            estimated_tokens=0,
        )

    # 摘要优先占用预算，剩余部分留给原文轮次，至少保留一轮的额度
    history_budget = max(
        budget_tokens - summary_tokens, Defaults.CHAT_CONTEXT_MIN_ROUND_TOKENS
    )

    trimmed = trim_chat_history(history, config, history_budget)
    window = trimmed.history
    # 未进入注入窗口的更早轮次即为待折叠对象
    foldable_rounds = history[: len(history) - len(window)]
    total_tokens = summary_tokens + _rounds_tokens(history)
    near_limit = _budgeted_tokens(total_tokens, config) > (
        budget_tokens * config.compact_trigger_ratio
    )

    if foldable_rounds:
        compact_targets = foldable_rounds
    elif near_limit and len(window) > config.keep_rounds:
        # 尚未溢出但已接近预算，提前折叠保留窗口之外的轮次；
        # 这些轮次本轮仍在注入窗口内，会与本轮生成的摘要重复一次，下一轮水位线生效后消失
        compact_targets = history[: len(history) - config.keep_rounds]
    else:
        compact_targets = []

    injected_tokens = summary_tokens + _rounds_tokens(window)
    return ContextPlan(
        summary=summary_text,
        history=window,
        compact_targets=compact_targets,
        budget_tokens=budget_tokens,
        estimated_tokens=_budgeted_tokens(injected_tokens, config),
    )


def trim_chat_history(
    history: list[ChatHistoryItem], config: ContextBudgetConfig, max_tokens: int
) -> ContextTrimResult:
    """按 token 预算裁剪聊天历史

    裁剪顺序：
    1. 候选轮数超出上限时只保留最近的若干轮
    2. 单条消息按字符上限收敛，避免单条超长回复占满预算
    3. 先保留最近 keep_rounds 轮，再在预算内向前扩展更早的轮次
    4. 保留窗口自身超预算时，从最旧一轮开始丢弃
    5. 仅剩一轮仍超预算时，按剩余额度截断该轮内容

    Args:
        history: 按旧到新排列的历史对话
        config: 上下文预算配置
        max_tokens: 本次可用于历史的估算 token 预算

    Returns:
        ContextTrimResult: 裁剪后的历史、估算 token 数与丢弃轮数
    """
    if not history:
        return ContextTrimResult(
            history=[], estimated_tokens=0, dropped_rounds=0, truncated=False
        )

    candidate_rounds = list(history)[-config.candidate_rounds :]
    normalized_rounds: list[ChatHistoryItem] = []
    truncated = False
    for item in candidate_rounds:
        normalized = _truncate_round(item, config.single_message_chars)
        if normalized != item:
            truncated = True
        normalized_rounds.append(normalized)

    keep_rounds = min(config.keep_rounds, len(normalized_rounds))
    window = list(normalized_rounds[len(normalized_rounds) - keep_rounds :])
    window_tokens = _rounds_tokens(window)

    # 在预算内向前扩展更早的轮次，越旧优先级越低
    index = len(normalized_rounds) - keep_rounds - 1
    while index >= 0:
        candidate_tokens = _rounds_tokens([normalized_rounds[index]])
        if not _within_budget(window_tokens + candidate_tokens, max_tokens, config):
            break
        window.insert(0, normalized_rounds[index])
        window_tokens += candidate_tokens
        index -= 1

    # 保留窗口自身超预算时从最旧一轮开始丢弃，保证最新一轮始终在窗口内
    while len(window) > 1 and not _within_budget(window_tokens, max_tokens, config):
        window_tokens -= _rounds_tokens([window.pop(0)])

    # 仅剩一轮仍超预算时按剩余额度截断，避免极端情况下上下文完全为空
    if window and not _within_budget(window_tokens, max_tokens, config):
        window[0] = _fit_round_to_budget(window[0], max_tokens, config)
        window_tokens = _rounds_tokens(window)
        truncated = True

    return ContextTrimResult(
        history=window,
        estimated_tokens=_budgeted_tokens(window_tokens, config),
        # 丢弃轮数按原始输入统计，候选上限与预算裁剪都计入
        dropped_rounds=len(history) - len(window),
        truncated=truncated,
    )


def _is_cjk(char: str) -> bool:
    """判断字符是否属于中日韩全角字符范围"""
    code = ord(char)
    return (
        0x3000 <= code <= 0x303F  # 中文标点
        or 0x3040 <= code <= 0x30FF  # 日文假名
        or 0x3400 <= code <= 0x4DBF  # 汉字扩展 A
        or 0x4E00 <= code <= 0x9FFF  # 基本汉字
        or 0xF900 <= code <= 0xFAFF  # 兼容汉字
        or 0xFF00 <= code <= 0xFFEF  # 全角字符
    )


def _summary_tokens(summary: str) -> int:
    """统计摘要占用的 token，含固定消息开销"""
    if not summary:
        return 0
    return estimate_tokens(summary) + Defaults.CHAT_CONTEXT_MESSAGE_OVERHEAD_TOKENS * 2


def _rounds_tokens(rounds: list[ChatHistoryItem]) -> int:
    """统计若干轮对话的 token 估算总量"""
    return sum(
        estimate_tokens(ask)
        + estimate_tokens(reply)
        + Defaults.CHAT_CONTEXT_MESSAGE_OVERHEAD_TOKENS * 2
        for ask, reply in rounds
    )


def _budgeted_tokens(tokens: int, config: ContextBudgetConfig) -> int:
    """按安全系数放大估算值，得到参与预算判断的保守 token 数"""
    return math.ceil(tokens * config.safety_ratio)


def _within_budget(tokens: int, max_tokens: int, config: ContextBudgetConfig) -> bool:
    """判断估算 token 数是否在预算内"""
    return _budgeted_tokens(tokens, config) <= max_tokens


def _truncate_round(item: ChatHistoryItem, max_chars: int) -> ChatHistoryItem:
    """按字符上限收敛单轮内容"""
    ask, reply = item
    return (_truncate_text(ask, max_chars), _truncate_text(reply, max_chars))


def _truncate_text(text: str, max_chars: int) -> str:
    """截断文本并追加截断标记"""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    suffix = Defaults.CHAT_CONTEXT_TRUNCATED_SUFFIX
    keep_chars = max(max_chars - len(suffix), 0)
    return text[:keep_chars] + suffix


def _fit_round_to_budget(
    item: ChatHistoryItem, max_tokens: int, config: ContextBudgetConfig
) -> ChatHistoryItem:
    """按剩余额度压缩单轮内容，优先保留用户提问

    保守按 1 字符 1 token 折算可用字符数，确保截断后必然落在预算内
    """
    safe_ratio = max(config.safety_ratio, 1.0)
    allowed_chars = max(
        int(max_tokens / safe_ratio)
        - Defaults.CHAT_CONTEXT_MESSAGE_OVERHEAD_TOKENS * 2,
        Defaults.CHAT_CONTEXT_MIN_ROUND_TOKENS,
    )
    ask, reply = item
    truncated_ask = _truncate_text(ask, allowed_chars)
    remaining_chars = max(allowed_chars - len(truncated_ask), 0)
    return (truncated_ask, _truncate_text(reply, remaining_chars))


def _positive_int(value: Any, fallback: int) -> int:
    """转换为正整数，非法或非正值回退默认值"""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _positive_float(value: Any, fallback: float) -> float:
    """转换为正浮点数，非法或非正值回退默认值"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _ratio(value: Any, fallback: float) -> float:
    """转换为 0 到 1 之间的比例，非法或越界时回退默认值"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if 0 < parsed <= 1 else fallback
