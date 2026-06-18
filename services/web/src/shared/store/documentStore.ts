import { create } from "zustand";
import { apiClient } from "@/shared/api/client";
import { useAuthStore } from "@/shared/store/authStore";
import type {
  DocumentResponse,
  BlockMetaResponse,
  ProposalResponse,
  ArbitrationResponse,
  PoolStatusResponse,
} from "@/shared/types/contracts";
import { DocumentState, BlockTag, ProposalStatus } from "@/shared/types/contracts";

interface DocumentStoreState {
  documents: DocumentResponse[];
  currentDoc: DocumentResponse | null;
  blockMetas: BlockMetaResponse[];
  proposals: ProposalResponse[];
  arbitrations: ArbitrationResponse[];
  poolStatus: PoolStatusResponse | null;

  fetchDocuments: () => Promise<void>;
  fetchDocument: (docId: string) => Promise<void>;
  createDocument: (data: {
    title: string;
    anchor_statement: string;
    anchor_audience: string;
    anchor_argument: string;
  }) => Promise<DocumentResponse>;
  transitionState: (docId: string, toState: DocumentState) => Promise<void>;
  fetchBlockMetas: (docId: string) => Promise<void>;
  claimBlock: (docId: string, blockId: string) => Promise<void>;
  fetchProposals: (docId: string, aiSourceType?: string) => Promise<void>;
  requestForge: (
    docId: string,
    blockId: string,
    instruction: string,
    aiSource: string
  ) => Promise<ProposalResponse>;
  approveProposal: (propId: string, action: string) => Promise<void>;
  fetchPoolStatus: () => Promise<void>;
  fetchArbitrations: (docId: string) => Promise<void>;
}

export const useDocumentStore = create<DocumentStoreState>((set) => ({
  documents: [],
  currentDoc: null,
  blockMetas: [],
  proposals: [],
  arbitrations: [],
  poolStatus: null,

  fetchDocuments: async () => {
    const docs = await apiClient.get<DocumentResponse[]>("/api/documents");
    set({ documents: docs });
  },

  fetchDocument: async (docId) => {
    const doc = await apiClient.get<DocumentResponse>(`/api/documents/${docId}`);
    set({ currentDoc: doc });

    if (useAuthStore.getState().isAuthenticated) {
      await useAuthStore.getState().setDocRole(docId);
    }
  },

  createDocument: async (data) => {
    const doc = await apiClient.post<DocumentResponse>("/api/documents", data);
    set((state) => ({ documents: [...state.documents, doc] }));
    return doc;
  },

  transitionState: async (docId, toState) => {
    await apiClient.put(`/api/documents/${docId}/state`, { state: toState });
    set((state) => ({
      currentDoc: state.currentDoc?.doc_id === docId
        ? { ...state.currentDoc, state: toState }
        : state.currentDoc,
      documents: state.documents.map((d) =>
        d.doc_id === docId ? { ...d, state: toState } : d
      ),
    }));
  },

  fetchBlockMetas: async (docId) => {
    const metas = await apiClient.get<BlockMetaResponse[]>(`/api/documents/${docId}/blocks`);
    set({ blockMetas: metas });
  },

  claimBlock: async (docId, blockId) => {
    await apiClient.post(`/api/documents/${docId}/blocks/${blockId}/claim`);
    set((state) => ({
      blockMetas: state.blockMetas.map((b) =>
        b.block_id === blockId
          ? { ...b, tags: [...b.tags.filter((t) => t !== BlockTag.CLAIMED), BlockTag.CLAIMED] }
          : b
      ),
    }));
  },

  fetchProposals: async (docId, aiSourceType) => {
    const params = aiSourceType ? `?ai_source_type=${aiSourceType}` : "";
    const proposals = await apiClient.get<ProposalResponse[]>(
      `/api/documents/${docId}/proposals${params}`
    );
    set({ proposals });
  },

  requestForge: async (docId, blockId, instruction, aiSource) => {
    const proposal = await apiClient.post<ProposalResponse>(
      `/api/documents/${docId}/blocks/${blockId}/forge`,
      { instruction, ai_source: aiSource }
    );
    set((state) => ({ proposals: [...state.proposals, proposal] }));
    return proposal;
  },

  approveProposal: async (propId, action) => {
    await apiClient.post(`/api/proposals/${propId}/approve`, { action });
    set((state) => ({
      proposals: state.proposals.map((p) =>
        p.proposal_id === propId
          ? {
              ...p,
              status:
                action === "accept"
                  ? ProposalStatus.ACCEPTED
                  : ProposalStatus.REJECTED,
            }
          : p
      ),
    }));
  },

  fetchPoolStatus: async () => {
    const status = await apiClient.get<PoolStatusResponse>("/api/pool/status");
    set({ poolStatus: status });
  },

  fetchArbitrations: async (docId) => {
    const arbs = await apiClient.get<ArbitrationResponse[]>(
      `/api/documents/${docId}/arbitrations`
    );
    set({ arbitrations: arbs });
  },
}));
