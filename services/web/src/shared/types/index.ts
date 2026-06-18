import { DocumentState } from './contracts';

export {
  DocumentState,
  UserRole,
  BlockTag,
  ProposalStatus,
  ConflictType,
} from './contracts';

export type {
  UserResponse,
  TokenResponse,
  DocumentResponse,
  BlockMetaResponse,
  ProposalResponse,
  ArbitrationResponse,
  PoolStatusResponse,
  MemoryResponse,
  OperationLogResponse,
} from './contracts';

export interface StoredDocument {
  docId: string;
  title: string;
  state: DocumentState;
  statement: string;
  docType: string;
  collaborationMode: 'heavy' | 'light';
  targetAudience: string;
  coreArgument: string;
  ownerId: string;
  ownerName: string;
  collaboratorsCount: number;
  lastModified: string;
  createdAt: string;
  wordCount: number;
  blockIds: string[];
}

export interface BlockMeta {
  blockId: string;
  docId: string;
  tags: string[];
  claimantId: string;
  driftScore: number;
  lockedBy: string;
  content: string;
  order: number;
}

export interface AIProposal {
  proposalId: string;
  blockId: string;
  docId: string;
  aiSource: string;
  aiMemoryType: 'public' | 'private';
  oldContent: string;
  newContent: string;
  rationale: string;
  anchorAlignmentScore: number;
  createdAt: string;
  status: 'pending' | 'accepted' | 'rejected' | 'conflicted';
}

export const STATE_LABELS: Record<string, string> = {
  draft: '草稿态',
  discussion: '讨论态',
  review: '审查态',
  finalized: '定稿态',
  archived: '归档态',
};

export const STATE_ORDER: string[] = [
  'draft',
  'discussion',
  'review',
  'finalized',
  'archived',
];

export const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  draft: ['discussion', 'review'],
  discussion: ['review', 'draft'],
  review: ['finalized', 'discussion', 'draft'],
  finalized: ['draft', 'archived'],
  archived: [],
};
