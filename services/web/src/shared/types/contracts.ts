// ⚠️ AUTO-GENERATED from contracts/contracts.py
// 单一真相源 — 请勿手动编辑此文件
// 运行: make types

export enum DocumentState {
  DRAFT = "draft",
  DISCUSSION = "discussion",
  REVIEW = "review",
  FINALIZED = "finalized",
  ARCHIVED = "archived",
}

export enum GlobalRole {
  PERSONAL = "personal",
  TEAM_ADMIN = "team_admin",
  OPS = "ops",
}

export enum UserRole {
  OWNER = "owner",
  LEAD_EDITOR = "lead_editor",
  EDITOR = "editor",
  REVIEWER = "reviewer",
  READER = "reader",
}

export enum BlockTag {
  LOCKED_BY_HUMAN = "locked-by-human",
  DUAL_TRACK = "dual-track",
  CLAIMED = "claimed",
  DRIFT_WARNING = "drift-warning",
}

export enum AIMemoryType {
  PUBLIC = "public",
  PRIVATE = "private",
}

export enum ProposalStatus {
  PENDING = "pending",
  ACCEPTED = "accepted",
  REJECTED = "rejected",
  CONFLICTED = "conflicted",
}

export enum ReviewDimension {
  EXPRESSION_PRECISION = "expression_precision",
  POSITION_CONSISTENCY = "position_consistency",
}

export enum ApprovalAction {
  MERGE_ALL = "merge_all",
  REJECT_ANNOTATE = "reject_annotate",
  MANUAL_EDIT = "manual_edit",
}

export enum ArbitrationResolution {
  PROPOSAL_A = "proposal_a",
  PROPOSAL_B = "proposal_b",
  DECLINED = "declined",
}

export enum ConflictType {
  PURE_PERSONAL = "pure_personal",
  PURE_DOC_AI = "pure_doc_ai",
  MIXED = "mixed",
}

export interface Anchor {
  statement: string;
  target_audience: string;
  core_argument: string;
  version?: number;
  created_by?: string;
  created_at?: string;
  history?: string[];
}

export interface BlockMeta {
  block_id: string;
  doc_id: string;
  tags?: BlockTag[];
  claimant_id?: string;
  drift_score?: number;
  locked_by?: string;
}

export interface AIProposal {
  block_id: string;
  doc_id: string;
  ai_source: string;
  ai_memory_type: AIMemoryType;
  old_content: string;
  new_content: string;
  rationale: string;
  proposal_id?: string;
  anchor_alignment_score?: number;
  created_at?: string;
  status?: ProposalStatus;
}

export interface ReviewResult {
  doc_id: string;
  snapshot_id: string;
  reviewer_id: string;
  reviewer_type: string;
  dimension: ReviewDimension;
  verdict: string;
  review_id?: string;
  comment?: string;
  created_at?: string;
}

export interface ConflictArbitration {
  doc_id: string;
  block_id: string;
  conflict_type: ConflictType;
  proposals: string[];
  ai_sources: string[];
  arb_id?: string;
  claimant_id?: string;
  resolution?: ArbitrationResolution | null;
  decider_id?: string;
  decider_reason?: string;
  resolved_at?: string;
}

export interface Snapshot {
  doc_id: string;
  state: DocumentState;
  yjs_snapshot: Uint8Array;
  block_metas: BlockMeta[];
  anchor: Anchor;
  snap_id?: string;
  created_by?: string;
  created_at?: string;
}

export interface OperationLog {
  user_id: string;
  action: string;
  target_type: string;
  target_id: string;
  doc_id: string;
  op_id?: string;
  before_state?: string;
  after_state?: string;
  timestamp?: string;
}

export interface User {
  user_id: string;
  display_name: string;
  role: UserRole;
  created_at?: string;
}

export interface DocumentPermission {
  doc_id: string;
  user_id: string;
  effective_role: UserRole;
  joined_at?: string;
  invited_by?: string;
}

export enum WSMessageType {
  STATE_CHANGE = "state_change",
  DRIFT_ALERT = "drift_alert",
  CONFLICT_DETECTED = "conflict_detected",
  ARBITRATION_RESOLVED = "arbitration_resolved",
  PROPOSAL_CREATED = "proposal_created",
  PROPOSAL_UPDATED = "proposal_updated",
  REVIEW_STARTED = "review_started",
  REVIEW_COMPLETED = "review_completed",
  APPROVAL_CHANGED = "approval_changed",
  PAGINATION_SYNC = "pagination_sync",
  PING = "ping",
  PONG = "pong",
}

export interface WSMessage {
  type: WSMessageType;
  doc_id: string;
  payload?: Record<string, unknown>;
  sender_id?: string;
  timestamp?: string;
}

export interface LLMForgeRequest {
  anchor: Anchor;
  block_content: string;
  block_context: string;
  ai_role: string;
  memory_context: string;
  instruction: string;
}

export interface LLMForgeResponse {
  proposal_text: string;
  diff_summary: string;
  rationale: string;
  anchor_alignment_score: number;
}

export interface LLMReviewRequest {
  anchor: Anchor;
  snapshot_content: string;
  dimension: ReviewDimension;
  ai_role: string;
  memory_context: string;
}

export interface LLMReviewResponse {
  verdict: string;
  issues: string[];
  suggestions: string[];
}

export interface LLMConflictDetectRequest {
  anchor: Anchor;
  proposal_a: string;
  proposal_a_rationale: string;
  proposal_b: string;
  proposal_b_rationale: string;
}

export interface LLMConflictDetectResponse {
  is_opposing: boolean;
  conflict_description: string;
  dimension: string;
}

// ------------------------------------------------------------------
// API Response 包装类型（与后端 Pydantic schema 对齐，非 generator 产出）
// ------------------------------------------------------------------

export interface UserResponse {
  user_id: string;
  display_name: string;
  email: string;
  role: UserRole;
  global_role: GlobalRole;
  doc_role?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: UserResponse;
}

export interface DocumentResponse {
  doc_id: string;
  title: string;
  state: DocumentState;
  owner_id: string;
  anchor_statement: string;
  anchor_audience: string;
  anchor_argument: string;
  anchor_version: number;
  created_at: string;
  updated_at: string;
}

export interface BlockMetaResponse {
  block_id: string;
  doc_id: string;
  tags: BlockTag[];
  claimant_id: string;
  drift_score: number;
  locked_by: string;
  sort_order: number;
}

export interface ProposalResponse {
  proposal_id: string;
  block_id: string;
  doc_id: string;
  ai_source: string;
  ai_memory_type: string;
  old_content: string;
  new_content: string;
  rationale: string;
  anchor_alignment_score: number;
  diff_summary: string;
  created_at: string;
  status: ProposalStatus;
}

export interface ArbitrationResponse {
  arb_id: string;
  doc_id: string;
  block_id: string;
  conflict_type: ConflictType;
  proposals: string[];
  ai_sources: string[];
  claimant_id: string;
  resolution: string | null;
  decider_id: string;
  decider_reason: string;
  resolved_at: string | null;
}

export interface PoolStatusResponse {
  public_count: number;
  private_count: number;
  public_limit: number;
  private_limit: number;
  global_private_count: number;
  global_private_limit: number;
}

export interface MemoryResponse {
  rule: string;
  solidified: boolean;
  trigger_count: number;
  ai_role: string;
  memory_type: string;
}

export interface OperationLogResponse {
  op_id: string;
  user_id: string;
  action: string;
  target_type: string;
  target_id: string;
  doc_id: string;
  timestamp: string;
}
