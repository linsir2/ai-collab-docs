// AUTO-GENERATED from designs/openapi.yml
// DO NOT EDIT MANUALLY.
// Run: python contracts/gen_ts_types.py
// Source: designs/openapi.yml


// ── Enums ──

// AI记忆公私域隔离
export enum AIMemoryType {
  PUBLIC = "public",
  PRIVATE = "private",
}

// 审批操作：merge_all=全盘合并, reject_annotate=拒绝批注, manual_edit=手动编辑
export enum ApprovalAction {
  MERGE_ALL = "merge_all",
  REJECT_ANNOTATE = "reject_annotate",
  MANUAL_EDIT = "manual_edit",
}

// 仲裁裁决
export enum ArbitrationResolution {
  PROPOSAL_A = "proposal_a",
  PROPOSAL_B = "proposal_b",
  DECLINED = "declined",
}

// Block标签：locked-by-human=人类锁定AI不可提案, dual-track=公私双轨对标, claimed=段落已认领, drift-warning=立意漂移预警
export enum BlockTag {
  LOCKED_BY_HUMAN = "locked-by-human",
  DUAL_TRACK = "dual-track",
  CLAIMED = "claimed",
  DRIFT_WARNING = "drift-warning",
}

// 冲突类型：pure_personal=纯个人AI(仅本人可见), pure_doc_ai=纯文档AI, mixed=混合冲突(全体可见带角色标签)
export enum ConflictType {
  PURE_PERSONAL = "pure_personal",
  PURE_DOC_AI = "pure_doc_ai",
  MIXED = "mixed",
}

// 文档生命周期状态：draft=草稿态, discussion=讨论态, review=审查态, finalized=定稿态, archived=归档态
export enum DocumentState {
  DRAFT = "draft",
  DISCUSSION = "discussion",
  REVIEW = "review",
  FINALIZED = "finalized",
  ARCHIVED = "archived",
}

// 立意漂移状态。normal=正常, warning=连续3次<0.85(审查态不可定稿), blocked=<0.8(硬拦截，需人类重新锚定)
export enum DriftStatus {
  NORMAL = "normal",
  WARNING = "warning",
  BLOCKED = "blocked",
}

// 提案状态
export enum ProposalStatus {
  PENDING = "pending",
  ACCEPTED = "accepted",
  REJECTED = "rejected",
  CONFLICTED = "conflicted",
}

// 审查维度 (MVP仅2维：表述精准 + 立场一致)
export enum ReviewDimension {
  EXPRESSION_PRECISION = "expression_precision",
  POSITION_CONSISTENCY = "position_consistency",
}

// AI触发模式：manual=用户手动触发, auto=文档AI监听变更自动触发
export enum TriggerMode {
  MANUAL = "manual",
  AUTO = "auto",
}

// 五级人类权限
export enum UserRole {
  OWNER = "owner",
  LEAD_EDITOR = "lead_editor",
  EDITOR = "editor",
  REVIEWER = "reviewer",
  READER = "reader",
}

// ── Interfaces ──

// AI反馈条目 — 人类对AI提案的采纳/拒绝反馈记录
export interface AIFeedbackEntry {
  proposal_id: string;
  action: string;
  human_feedback?: string;
  timestamp?: string;
}

// AI记忆 — 公私域隔离。六层隔离：存储/访问/写入/可见性/生命周期/固化≥3次。
export interface AIMemory {
  memory_id: string;
  ai_source: string;
  memory_type: AIMemoryType;
  doc_id: string;
  feedback_log?: Array<AIFeedbackEntry>;
  approval_history?: Array<string>;
  rejection_history?: Array<string>;
  long_term_patterns?: Array<string>;
  trust_score?: number;
  created_at?: string;
  updated_at?: string;
}

// 立意锚 — 文档唯一锚点。创建时必填，所有AI能力/修改必须对齐此锚。仅Owner可修改。
export interface Anchor {
  statement: string;
  target_audience: string;
  core_argument: string;
  version: number;
  version_history?: Array<AnchorVersionRecord>;
  created_by?: string;
  created_at?: string;
}

// Anchor 版本历史记录
export interface AnchorVersionRecord {
  version: number;
  statement: string;
  updated_at?: string;
  updated_by?: string;
}

// Block视图 — 聚合BlockMeta + 内容预览。实际内容通过Yjs同步。
export interface Block {
  block_id: string;
  doc_id: string;
  order: number;
  content_preview?: string;
  meta?: BlockMeta;
}

// Block元数据 — 存储在PostgreSQL的外挂结构化标签。block_id/doc_id/order在Block层，不在此重复。
export interface BlockMeta {
  tags?: Array<BlockTag>;
  claimant_id?: string;
  drift_score?: number;
  version?: number;
  created_at?: string;
  updated_at?: string;
}

// 冲突仲裁 — 2+AI提案对立时触发。段落认领人有优先裁决权，无人认领沿决策上浮链。
export interface ConflictArbitration {
  arb_id: string;
  doc_id: string;
  block_id: string;
  conflict_type: ConflictType;
  proposals: Array<string>;
  ai_sources?: Array<string>;
  claimant_id?: string;
  resolution?: ArbitrationResolution;
  decider_id?: string;
  decider_reason?: string;
  resolved_at?: string;
}

// 文档聚合根 — BC1核心实体。状态流转受StateEngine约束，Block内容走Yjs同步。
export interface Document {
  doc_id: string;
  title?: string;
  anchor: Anchor;
  state: DocumentState;
  mode?: string;
  owner_id: string;
  block_count?: number;
  proposal_count_public?: number;
  proposal_count_private?: number;
  drift_status?: DriftStatus;
  tags?: Array<BlockTag>;
  created_at?: string;
  updated_at?: string;
  archived_at?: string;
}

// 文档级权限 — 用户在特定文档中的实际角色。不变量：effective_role ≤ User.role。
export interface DocumentPermission {
  doc_id: string;
  user_id: string;
  effective_role: UserRole;
  joined_at?: string;
  invited_by?: string;
}

// 
export interface Error {
  code: string;
  message: string;
  detail?: string;
}

// 操作日志 — 不可删除不可篡改。AuditService唯一写入者。
export interface OperationLog {
  op_id: string;
  user_id: string;
  action: string;
  target_type: string;
  target_id: string;
  doc_id: string;
  before_state?: string;
  after_state?: string;
  timestamp: string;
}

// 提案池容量统计 — 双轨AI的公私池计数与三级预警（80%橙/95%弹窗/100%阻断）
export interface PoolStats {
  public_count: number;
  private_count: number;
  public_limit: number;
  private_limit: number;
  global_count?: number;
  public_warning?: boolean;
  private_warning?: boolean;
  public_popup?: boolean;
  private_popup?: boolean;
  public_blocked?: boolean;
  private_blocked?: boolean;
  global_blocked?: boolean;
}

// AI提案 — AI零直改权限：仅提案/批注/争议举证，无直接修改权。
export interface Proposal {
  prop_id: string;
  doc_id: string;
  block_id: string;
  ai_source: string;
  ai_role?: string;
  content_before: string;
  content_after: string;
  rationale: string;
  anchor_alignment_score?: number;
  status: ProposalStatus;
  memory_type?: AIMemoryType;
  created_by?: string;
  created_at?: string;
  resolved_at?: string;
  resolved_by?: string;
}

// 文档快照 — 审查态入口创建，冻结当时文档状态。不可修改。
export interface Snapshot {
  snap_id: string;
  doc_id: string;
  state: DocumentState;
  yjs_snapshot?: string;
  block_metas?: Array<BlockMeta>;
  anchor?: Anchor;
  created_by: string;
  created_at?: string;
}

// 状态流转请求 — 受TRANSITION_MATRIX权限约束
export interface TransitionRequest {
  target_state: DocumentState;
  reason?: string;
}

// 用户 — Auth BC聚合根。文档级权限见DocumentPermission。
export interface User {
  user_id: string;
  display_name: string;
  email?: string;
  role: UserRole;
  created_at?: string;
}
