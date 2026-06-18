import { GlobalRole, UserRole } from "./types/contracts";

export { GlobalRole, UserRole };
export type DocRole = UserRole;

export enum ViewType {
  FORGE = "forge",
  TEAM = "team",
  OPS = "ops",
}

export enum MenuGroup {
  FORGE_TOOLS = "forge_tools",
  TEAM_MGMT = "team_mgmt",
  OPS_MONITOR = "ops_monitor",
}

// ============================================================
// 1. 视图与菜单权限
// ============================================================

const VIEW_ACCESS: Record<GlobalRole, Set<ViewType>> = {
  [GlobalRole.PERSONAL]: new Set([ViewType.FORGE]),
  [GlobalRole.TEAM_ADMIN]: new Set([ViewType.FORGE, ViewType.TEAM]),
  [GlobalRole.OPS]: new Set([ViewType.FORGE, ViewType.TEAM, ViewType.OPS]),
};

const MENU_GROUPS_BY_VIEW: Record<ViewType, Partial<Record<GlobalRole, MenuGroup[]>>> = {
  [ViewType.FORGE]: {
    [GlobalRole.PERSONAL]: [MenuGroup.FORGE_TOOLS],
    [GlobalRole.TEAM_ADMIN]: [MenuGroup.FORGE_TOOLS, MenuGroup.TEAM_MGMT],
    [GlobalRole.OPS]: [MenuGroup.FORGE_TOOLS, MenuGroup.TEAM_MGMT, MenuGroup.OPS_MONITOR],
  },
  [ViewType.TEAM]: {
    [GlobalRole.TEAM_ADMIN]: [MenuGroup.TEAM_MGMT],
    [GlobalRole.OPS]: [MenuGroup.TEAM_MGMT, MenuGroup.OPS_MONITOR],
  },
  [ViewType.OPS]: {
    [GlobalRole.OPS]: [MenuGroup.OPS_MONITOR],
  },
};

export function canAccessView(globalRole: GlobalRole, view: ViewType): boolean {
  return VIEW_ACCESS[globalRole]?.has(view) ?? false;
}

export function allowedViews(globalRole: GlobalRole): ViewType[] {
  return Object.values(ViewType).filter((view) => canAccessView(globalRole, view));
}

export function allowedMenuGroups(globalRole: GlobalRole, view: ViewType): MenuGroup[] {
  return MENU_GROUPS_BY_VIEW[view]?.[globalRole] ?? [];
}

// ============================================================
// 2. 文档内操作权限
// ============================================================

const DOC_ACTIONS: Record<string, Set<DocRole>> = {
  state_transition: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR]),
  archive: new Set([UserRole.OWNER]),
  manage_members: new Set([UserRole.OWNER]),
  assign_paragraphs: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR]),
  reset_memory: new Set([UserRole.OWNER]),
  use_forge: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR, UserRole.EDITOR]),
  start_review: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR, UserRole.REVIEWER]),
  resolve_arbitration: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR]),
  discuss: new Set(Object.values(UserRole)),
  claim_paragraph: new Set([
    UserRole.OWNER,
    UserRole.LEAD_EDITOR,
    UserRole.EDITOR,
    UserRole.REVIEWER,
  ]),
};

export function canDoInDocument(docRole: DocRole | null, action: string): boolean {
  if (!docRole) return false
  const allowed = DOC_ACTIONS[action]
  if (!allowed) return false
  return allowed.has(docRole)
}

// ============================================================
// 3. WebSocket 消息发送权限
// ============================================================

const WS_MESSAGE_PERMISSIONS: Record<string, Set<DocRole>> = {
  STATE_CHANGE: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR]),
  PROPOSAL_CREATED: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR, UserRole.EDITOR]),
  CONFLICT_DETECTED: new Set([UserRole.OWNER, UserRole.LEAD_EDITOR, UserRole.REVIEWER]),
  AI_BROADCAST: new Set([
    UserRole.OWNER,
    UserRole.LEAD_EDITOR,
    UserRole.EDITOR,
    UserRole.REVIEWER,
  ]),
};

export function isAllowedWsMessage(docRole: DocRole, msgType: string): boolean {
  const allowed = WS_MESSAGE_PERMISSIONS[msgType.toUpperCase()];
  if (allowed === undefined) {
    return Object.values(UserRole).includes(docRole);
  }
  return allowed.has(docRole);
}

// ============================================================
// 4. 标签/展示文案辅助函数
// ============================================================

const GLOBAL_ROLE_LABELS: Record<GlobalRole, string> = {
  [GlobalRole.PERSONAL]: "个人用户",
  [GlobalRole.TEAM_ADMIN]: "团队管理员",
  [GlobalRole.OPS]: "运维管理员",
};

const DOC_ROLE_LABELS: Record<DocRole, string> = {
  [UserRole.OWNER]: "所有者",
  [UserRole.LEAD_EDITOR]: "主编辑",
  [UserRole.EDITOR]: "编辑者",
  [UserRole.REVIEWER]: "审查者",
  [UserRole.READER]: "只读成员",
};

export function formatGlobalRoleLabel(role: GlobalRole): string {
  return GLOBAL_ROLE_LABELS[role] ?? role;
}

export function formatDocRoleLabel(role: DocRole): string {
  return DOC_ROLE_LABELS[role] ?? role;
}

export function trustScoreLabel(score: number): string {
  if (score < 40) return "谨慎审批";
  if (score <= 75) return "适度信任";
  return "高度信任";
}

export function driftLabel(similarity: number): { label: string; colorClass: string } {
  if (similarity >= 0.85) return { label: "贴合", colorClass: "text-success" };
  if (similarity >= 0.6) return { label: "轻微跑偏", colorClass: "text-warning" };
  return { label: "严重偏离", colorClass: "text-danger" };
}

export function blockTagLabel(tag: string): string {
  const normalized = tag.toLowerCase().replace(/-/g, "_");
  const mapping: Record<string, string> = {
    locked_by_human: "锁定",
    locked: "锁定",
    lock: "锁定",
    drift_warning: "冲突",
    drift: "冲突",
    warn: "冲突",
    warning: "冲突",
    claimed: "已认领",
    claim: "已认领",
  };
  return mapping[normalized] ?? tag;
}

export function auditActionLabel(action: string): string {
  const mapping: Record<string, string> = {
    create_document: "创建文档",
    create_doc: "创建文档",
    state_transition: "状态流转",
    proposal_accepted: "采纳提案",
    proposal_rejected: "拒绝提案",
    ai_interrupted: "中断 AI",
    manage_members: "成员管理",
    archive: "归档文档",
    reset_memory: "重置记忆",
    start_review: "启动审查",
    resolve_arbitration: "仲裁裁决",
    assign_paragraphs: "分配段落",
    claim_paragraph: "认领段落",
    discuss: "参与讨论",
  };
  return mapping[action.toLowerCase()] ?? action;
}
