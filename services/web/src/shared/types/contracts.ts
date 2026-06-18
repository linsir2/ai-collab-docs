export enum DocumentState {
  DRAFT = "draft",
  DISCUSSION = "discussion",
  REVIEW = "review",
  FINALIZED = "finalized",
  ARCHIVED = "archived",
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

export enum ProposalStatus {
  PENDING = "pending",
  ACCEPTED = "accepted",
  REJECTED = "rejected",
  CONFLICTED = "conflicted",
}

export enum ConflictType {
  PURE_PERSONAL = "pure_personal",
  PURE_DOC_AI = "pure_doc_ai",
  MIXED = "mixed",
}

export interface UserResponse {
  user_id: string;
  display_name: string;
  email: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
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
