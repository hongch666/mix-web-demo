from app.internal.services.llm.contextBudget import (
    ChatHistoryItem,
    ContextBudgetConfig,
    estimate_tokens,
    plan_chat_context,
    plan_compact_batch,
    trim_chat_history,
)


def _budget(**overrides: object) -> ContextBudgetConfig:
    """构造预算配置，未指定项使用宽松默认值，避免用例互相干扰"""
    values: dict[str, object] = {
        "window_tokens": 100000,
        "output_reserve_tokens": 0,
        "tool_reserve_tokens": 0,
        "compact_trigger_ratio": 0.8,
        "keep_rounds": 2,
        "candidate_rounds": 10,
        "safety_ratio": 1.0,
        "single_message_chars": 1000,
        "summary_max_chars": 500,
        "compact_input_chars": 12000,
    }
    values.update(overrides)
    return ContextBudgetConfig(**values)  # type: ignore[arg-type]


def _rounds(count: int) -> list[ChatHistoryItem]:
    return [(f"q{index}", "答" * 40) for index in range(count)]


# CJK 字符按 1 字符 1 token 估算，非 CJK 字符按 4 字符 1 token 估算
def test_estimate_tokens_counts_cjk_more_than_ascii() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("中文") == 2
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("中文abcd") == 3


# 历史预算由模型窗口扣除提示词、输出预留与工具预留后推导
def test_history_budget_subtracts_prompt_and_reserves() -> None:
    config = _budget(
        window_tokens=10000,
        output_reserve_tokens=1000,
        tool_reserve_tokens=2000,
        safety_ratio=1.0,
    )

    assert config.history_budget(500) == 8500
    assert config.history_budget(500, use_tools=True) == 6500


# 预算按窗口扣除预留后原样返回，安全系数只在比较处折算，不做二次压缩
def test_history_budget_returns_raw_estimate_without_safety_ratio() -> None:
    config = _budget(
        window_tokens=10000,
        output_reserve_tokens=1000,
        tool_reserve_tokens=0,
        safety_ratio=1.25,
    )

    assert config.history_budget(500) == 10000 - 1000 - 500


# 安全系数在裁剪比较处生效一次，估算值放大后决定可注入的轮次
def test_trim_chat_history_applies_safety_ratio_once() -> None:
    history = _rounds(6)

    without_safety = trim_chat_history(
        history, _budget(safety_ratio=1.0, keep_rounds=1), 294
    )
    with_safety = trim_chat_history(
        history, _budget(safety_ratio=1.2, keep_rounds=1), 294
    )

    # 每轮约 49 tokens：预算 294 在放大 1.2 倍后只剩 5 轮的额度
    assert len(without_safety.history) == 6
    assert len(with_safety.history) == 5


# 预留超过窗口时返回 0，不出现负预算
def test_history_budget_returns_zero_when_window_exhausted() -> None:
    config = _budget(window_tokens=100, output_reserve_tokens=1000, safety_ratio=1.0)

    assert config.history_budget(0) == 0


# 预算为 0 时不注入摘要与历史，也不产生压缩对象
def test_plan_chat_context_returns_empty_plan_when_budget_exhausted() -> None:
    config = _budget(window_tokens=100, output_reserve_tokens=1000)

    plan = plan_chat_context("已存摘要", _rounds(5), config, prompt_tokens=0)

    assert plan.summary == ""
    assert plan.history == []
    assert plan.compact_targets == []
    assert plan.should_compact is False
    assert plan.budget_tokens == 0


# 空历史直接返回空结果，不做任何预算计算
def test_trim_chat_history_returns_empty_for_empty_history() -> None:
    result = trim_chat_history([], _budget(), 100000)

    assert result.history == []
    assert result.estimated_tokens == 0
    assert result.dropped_rounds == 0
    assert result.truncated is False


# 候选轮数超出上限时只保留最近的若干轮，丢弃轮数按原始输入统计
def test_trim_chat_history_caps_candidate_rounds_keeping_recent() -> None:
    history = [(f"问题{index}", f"回答{index}") for index in range(10)]

    result = trim_chat_history(
        history, _budget(candidate_rounds=3, keep_rounds=1), 100000
    )

    assert [ask for ask, _reply in result.history] == ["问题7", "问题8", "问题9"]
    assert result.dropped_rounds == 7


# 超出 token 预算时保留最近保留轮数，不再向前扩展更早的轮次
def test_trim_chat_history_drops_oldest_rounds_when_over_budget() -> None:
    history = _rounds(6)

    result = trim_chat_history(
        history, _budget(keep_rounds=2, candidate_rounds=10), 120
    )

    assert [ask for ask, _reply in result.history] == ["q4", "q5"]
    assert result.dropped_rounds == 4
    assert result.estimated_tokens <= 120


# 单条超长回复先按字符上限收敛，避免挤占整段上下文预算
def test_trim_chat_history_truncates_oversized_single_message() -> None:
    history = [("问题", "答" * 500)]

    result = trim_chat_history(
        history,
        _budget(candidate_rounds=1, keep_rounds=1, single_message_chars=50),
        100000,
    )

    reply = result.history[0][1]
    assert reply.endswith("...")
    assert len(reply) == 50
    assert result.truncated is True


# 仅剩一轮仍超预算时按剩余额度截断，用户提问优先保留
def test_trim_chat_history_fits_last_round_when_budget_tight() -> None:
    history = [("问" * 50, "答" * 500)]

    result = trim_chat_history(
        history, _budget(keep_rounds=1, candidate_rounds=1, safety_ratio=1.0), 80
    )

    assert result.history[0][0] == "问" * 50
    assert result.history[0][1].endswith("...")
    assert result.estimated_tokens <= 80
    assert result.truncated is True


# 历史未超过预算且未接近触发比例时按原样注入，不产生压缩对象
def test_plan_chat_context_keeps_history_within_budget() -> None:
    history = [("q1", "a1"), ("q2", "a2"), ("q3", "a3")]

    plan = plan_chat_context("", history, _budget(), prompt_tokens=10)

    assert plan.should_compact is False
    assert plan.compact_targets == []
    assert plan.history == history


# 超出窗口预算时把窗口之外的更早轮次标记为待压缩
def test_plan_chat_context_compacts_when_over_budget() -> None:
    history = _rounds(6)
    config = _budget(window_tokens=200, keep_rounds=2, candidate_rounds=6)

    plan = plan_chat_context("", history, config, prompt_tokens=4, use_tools=True)

    # 每轮约 49 tokens，预算 196 只能容纳最近 4 轮
    assert plan.should_compact is True
    assert [ask for ask, _reply in plan.history] == ["q2", "q3", "q4", "q5"]
    assert [ask for ask, _reply in plan.compact_targets] == ["q0", "q1"]
    assert plan.estimated_tokens <= plan.budget_tokens


# 尚未溢出但占用达到触发比例时提前压缩，比例关闭则不压缩
def test_plan_chat_context_compacts_when_near_trigger_ratio() -> None:
    history = _rounds(40)
    config = _budget(window_tokens=2000, keep_rounds=1, candidate_rounds=40)

    plan = plan_chat_context("", history, config, prompt_tokens=0)

    assert plan.should_compact is True
    assert len(plan.history) == 40
    assert len(plan.compact_targets) == 39

    relaxed = plan_chat_context(
        "",
        history,
        _budget(
            window_tokens=2000,
            keep_rounds=1,
            candidate_rounds=40,
            compact_trigger_ratio=1.0,
        ),
        prompt_tokens=0,
    )
    assert relaxed.should_compact is False


# 摘要占用同一预算，摘要越长留给原文的额度越小
def test_plan_chat_context_summary_consumes_budget() -> None:
    summary = "摘" * 100
    history = _rounds(5)
    config = _budget(window_tokens=400, keep_rounds=1, candidate_rounds=5)

    plan = plan_chat_context(summary, history, config, prompt_tokens=0)

    assert plan.summary == summary
    assert plan.should_compact is True
    assert plan.budget_tokens == 400


# ===== 记忆压缩批次 =====


# 折叠内容按单次输入上限收敛，未纳入批次的记录留待下一轮
def test_plan_compact_batch_limits_input_by_chars() -> None:
    items = [(index, f"问{index}", "答" * 100) for index in range(1, 6)]
    config = _budget(compact_input_chars=250)

    batch = plan_compact_batch(items, config)

    # 每轮 102 字，上限 250 只能容纳最早的两轮
    assert batch.count == 2
    assert batch.last_id == 2
    assert [ask for ask, _reply in batch.rounds] == ["问1", "问2"]


# 单条超过字符上限时先截断，压缩输入不会因单条超长而失控
def test_plan_compact_batch_truncates_single_message() -> None:
    items = [(1, "问题", "答" * 500)]

    batch = plan_compact_batch(
        items, _budget(compact_input_chars=10000, single_message_chars=50)
    )

    assert batch.count == 1
    reply = batch.rounds[0][1]
    assert len(reply) == 50
    assert reply.endswith("...")


# 至少折叠一轮，输入上限小于单轮长度时压缩仍能推进
def test_plan_compact_batch_keeps_first_round_when_limit_too_small() -> None:
    items = [(1, "问题", "答" * 100), (2, "问题", "答" * 100)]

    batch = plan_compact_batch(items, _budget(compact_input_chars=10))

    assert batch.count == 1
    assert batch.last_id == 1


# 无可折叠内容时返回空批次，水位线不推进
def test_plan_compact_batch_returns_empty_for_no_items() -> None:
    batch = plan_compact_batch([], _budget())

    assert batch.rounds == []
    assert batch.count == 0
    assert batch.last_id == 0


# agent 配置缺失或非法时预算回退字段默认值，候选轮数不小于保留轮数
def test_context_budget_config_falls_back_to_defaults() -> None:
    defaults = ContextBudgetConfig()
    config = ContextBudgetConfig.from_agent_config(
        {
            "context_window_tokens": "非法值",
            "context_keep_rounds": 0,
            "context_candidate_rounds": 3,
            "context_compact_trigger_ratio": 2,
            "context_safety_ratio": -1,
            "context_single_message_chars": None,
            "context_compact_input_chars": 0,
        }
    )

    assert config.window_tokens == defaults.window_tokens
    assert config.keep_rounds == defaults.keep_rounds
    assert config.candidate_rounds == defaults.keep_rounds
    assert config.compact_trigger_ratio == defaults.compact_trigger_ratio
    assert config.safety_ratio == defaults.safety_ratio
    assert config.single_message_chars == defaults.single_message_chars
    assert config.compact_input_chars == defaults.compact_input_chars


# agent 配置合法时按配置构建预算，字符串数值同样可解析
def test_context_budget_config_reads_agent_config() -> None:
    config = ContextBudgetConfig.from_agent_config(
        {
            "context_window_tokens": "64000",
            "context_output_reserve_tokens": "1024",
            "context_tool_reserve_tokens": "2048",
            "context_compact_trigger_ratio": "0.6",
            "context_keep_rounds": "3",
            "context_candidate_rounds": "8",
            "context_safety_ratio": "1.5",
            "context_single_message_chars": "800",
            "context_summary_max_chars": "600",
            "context_compact_input_chars": "9000",
        }
    )

    assert config.window_tokens == 64000
    assert config.output_reserve_tokens == 1024
    assert config.tool_reserve_tokens == 2048
    assert config.compact_trigger_ratio == 0.6
    assert config.keep_rounds == 3
    assert config.candidate_rounds == 8
    assert config.safety_ratio == 1.5
    assert config.single_message_chars == 800
    assert config.summary_max_chars == 600
    assert config.compact_input_chars == 9000
