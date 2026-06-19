"""
LLM 输入/输出契约（内部类型，非REST API）
==========================================
项目: ai-collab-docs | 用于: ai_forge BC 的 llm_client
"""
from dataclasses import dataclass

from contracts._auto_enums import ReviewDimension
from contracts._auto_models import Anchor  # type: ignore[import-untyped]


@dataclass(frozen=True)
class LLMForgeRequest:
    """向LLM请求提案时的输入格式"""
    anchor: Anchor                          # 全量锚点上下文
    block_content: str                      # 当前Block内容
    block_context: str                      # 前后Block上下文（≥3段，含Diff高亮）
    ai_role: str                            # AI角色（Legal/Editor/Reviewer/Creative...）
    memory_context: str                     # 对应AIMemory的最近反馈摘要
    instruction: str                        # 用户指令（@触发时带上）


@dataclass(frozen=True)
class LLMForgeResponse:
    """LLM返回的提案"""
    proposal_text: str                      # 建议修改后的完整内容
    diff_summary: str                       # 变更摘要（人类可读）
    rationale: str                          # 修改理由
    anchor_alignment_score: float           # 与立意锚的对齐度（LLM自查）


@dataclass(frozen=True)
class LLMReviewRequest:
    """向LLM请求审查时的输入格式"""
    anchor: Anchor
    snapshot_content: str                   # 快照全文
    dimension: ReviewDimension
    ai_role: str
    memory_context: str


@dataclass(frozen=True)
class LLMReviewResponse:
    """LLM返回的审查结果"""
    verdict: str                            # "pass" | "fail" | "warning"
    issues: tuple[str, ...]                # 问题列表
    suggestions: tuple[str, ...]           # 建议列表


@dataclass(frozen=True)
class LLMConflictDetectRequest:
    """向LLM请求冲突检测时的输入格式"""
    anchor: Anchor
    proposal_a: str                         # 提案A内容
    proposal_a_rationale: str
    proposal_b: str                         # 提案B内容
    proposal_b_rationale: str


@dataclass(frozen=True)
class LLMConflictDetectResponse:
    """LLM返回的冲突检测结果"""
    is_opposing: bool                       # 是否对立
    conflict_description: str               # 冲突描述
    dimension: str                          # 冲突维度（内容/风格/立场）
