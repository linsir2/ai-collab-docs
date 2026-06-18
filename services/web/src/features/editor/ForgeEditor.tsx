import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import ForgeLayout from '../../layouts/ForgeLayout';
import StateAirlock from './StateAirlock';
import { useDocumentStore } from '../../shared/store/documentStore';
import { DocumentState } from '../../shared/types';
import type { BlockMetaResponse, ProposalResponse } from '@/shared/types/contracts';

const MOCK_CONTENTS: Record<string, string> = {
  'block-001': '## 背景与目标\n\n本文档旨在建立一套高效透明的资源调配机制，以应对2026年Q3日益增长的业务需求。',
  'block-002': '## 现状分析\n\n当前资源利用率约为78%，存在明显的峰谷波动。',
  'block-003': '## 优化方案\n\n提出三阶段优化策略：第一阶段（7月）完成资源池化改造。',
  'block-004': '## 实施路线图\n\n详细的时间表与里程碑：各阶段关键交付物、验收标准。',
  'block-005': '## 预期收益与风险\n\n预期ROI为320%，投资回收期6个月。',
};

export default function ForgeEditor() {
  const { docId } = useParams<{ docId: string }>();
  const currentDoc = useDocumentStore((s) => s.currentDoc);
  const blockMetas = useDocumentStore((s) => s.blockMetas);
  const proposals = useDocumentStore((s) => s.proposals);
  const fetchDocument = useDocumentStore((s) => s.fetchDocument);
  const fetchBlockMetas = useDocumentStore((s) => s.fetchBlockMetas);
  const fetchProposals = useDocumentStore((s) => s.fetchProposals);

  const [activeTab, setActiveTab] = useState<'private' | 'public'>('private');
  const [focusedBlock, setFocusedBlock] = useState<string | null>(null);
  const [blockContents, setBlockContents] = useState<Record<string, string>>({});
  const [aiRolePrivate, setAiRolePrivate] = useState('我的技术顾问');
  const [aiRolePublic, setAiRolePublic] = useState('TechReviewer');
  const [privateInput, setPrivateInput] = useState('');
  const [publicInput, setPublicInput] = useState('');

  useEffect(() => {
    if (docId) {
      fetchDocument(docId);
      fetchBlockMetas(docId);
      fetchProposals(docId);
    }
  }, [docId, fetchDocument, fetchBlockMetas, fetchProposals]);

  useEffect(() => {
    if (blockMetas.length > 0) {
      const contents: Record<string, string> = {};
      for (const b of blockMetas) {
        contents[b.block_id] = MOCK_CONTENTS[b.block_id] ?? '(内容加载中...)';
      }
      setBlockContents(contents);
    }
  }, [blockMetas]);

  const handleTransition = useCallback((_toState: DocumentState) => {
  }, []);

  const getBlockBorderStyle = (block: BlockMetaResponse): React.CSSProperties => {
    if (block.tags.includes('locked-by-human' as never)) {
      return { borderLeft: '2px solid var(--danger)' };
    }
    if (block.tags.includes('drift-warning' as never)) {
      return { borderLeft: '2px dashed var(--warning)' };
    }
    if (block.tags.includes('claimed' as never)) {
      return { borderLeft: '2px dotted var(--info)' };
    }
    return { borderLeft: '2px solid var(--border-subtle)' };
  };

  const getBlockTag = (block: BlockMetaResponse) => {
    const tags = block.tags as string[];
    if (tags.includes('locked-by-human')) {
      return (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--danger)', background: 'var(--danger-subtle)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>
          LOCK Locked-by-Human
        </span>
      );
    }
    if (tags.includes('drift-warning')) {
      return (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--warning)', background: 'var(--warning-subtle)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>
          WARN Drift-Warning
        </span>
      );
    }
    if (tags.includes('claimed')) {
      return (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--info)', background: 'var(--info-subtle)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>
          Claimed-by-{block.claimant_id || 'XX'}
        </span>
      );
    }
    return null;
  };

  const driftScore = 0.92;
  const getDriftColor = (score: number) => {
    if (score >= 0.9) return 'var(--success)';
    if (score >= 0.85) return 'var(--warning)';
    return 'var(--danger)';
  };

  const getDriftSegments = (score: number) => {
    const segs = Array(6).fill(false);
    if (score >= 0.95) segs.fill(true);
    else if (score >= 0.9) { segs[0] = segs[1] = segs[2] = segs[3] = segs[4] = true; }
    else if (score >= 0.85) { segs[0] = segs[1] = segs[2] = segs[3] = true; }
    else if (score >= 0.8) { segs[0] = segs[1] = segs[2] = true; }
    else { segs[0] = segs[1] = true; }
    return segs;
  };

  const privateProposals = proposals.filter((p) => p.ai_memory_type === 'private');
  const publicProposals = proposals.filter((p) => p.ai_memory_type === 'public');

  const leftPanel = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div
        style={{
          background: 'var(--bg-elevated)',
          borderLeft: '2px solid var(--accent)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
        }}
      >
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 'var(--space-2)' }}>
          立意锚
        </div>
        <p style={{ fontSize: 'var(--text-base)', color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: 'var(--space-2)' }}>
          {currentDoc?.anchor_statement || (currentDoc?.title ?? '加载中...')}
        </p>
        <div style={{ textAlign: 'right' }}>
          <a href="#" style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)' }} onClick={(e) => e.preventDefault()}>
            查看历史 →
          </a>
        </div>
      </div>

      <div
        style={{
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          border: '1px solid var(--border-default)',
        }}
      >
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 'var(--space-3)' }}>
          语义漂移检测仪 VU Meter
        </div>
        <div style={{ fontSize: 36, fontWeight: 700, fontFamily: 'var(--font-mono)', color: getDriftColor(driftScore), textAlign: 'center', marginBottom: 'var(--space-2)' }}>
          {driftScore.toFixed(2)}
        </div>
        <div style={{ display: 'flex', gap: 3, marginBottom: 'var(--space-2)' }}>
          {getDriftSegments(driftScore).map((active, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: 8,
                borderRadius: 2,
                background: active ? getDriftColor(driftScore) : 'var(--bg-surface)',
              }}
            />
          ))}
        </div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', textAlign: 'center' }}>
          状态: {driftScore >= 0.9 ? '稳定' : driftScore >= 0.85 ? '轻微' : '警告'}
        </div>
      </div>

      <div
        style={{
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          border: '1px solid var(--border-default)',
        }}
      >
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 'var(--space-3)' }}>
          文档结构树
        </div>
        {blockMetas.map((block, idx) => (
          <div
            key={block.block_id}
            onClick={() => setFocusedBlock(block.block_id)}
            style={{
              padding: 'var(--space-1) var(--space-2)',
              paddingLeft: `${idx * 8 + 12}px`,
              fontSize: 'var(--text-xs)',
              color: focusedBlock === block.block_id ? 'var(--accent)' : 'var(--text-secondary)',
              background: focusedBlock === block.block_id ? 'var(--accent-subtle)' : 'transparent',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              marginBottom: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
              transition: 'all 0.1s',
            }}
          >
            <span style={{ fontSize: 10 }}>
              {(block.tags as string[]).includes('locked-by-human') ? '🔒' :
               (block.tags as string[]).includes('drift-warning') ? '⚠️' :
               (block.tags as string[]).includes('claimed') ? '👤' : '📝'}
            </span>
            {block.block_id}
          </div>
        ))}
      </div>
    </div>
  );

  const centerPanel = (
    <div>
      <StateAirlock
        currentState={currentDoc?.state ?? DocumentState.DRAFT}
        onTransition={handleTransition}
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {blockMetas.map((block) => (
          <div
            key={block.block_id}
            style={{
              background: 'var(--bg-surface)',
              borderRadius: 'var(--radius-md)',
              border: focusedBlock === block.block_id ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
              ...getBlockBorderStyle(block),
              padding: 'var(--space-3)',
              transition: 'border-color 0.15s',
            }}
            onClick={() => setFocusedBlock(block.block_id)}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {block.block_id}
              </span>
              {getBlockTag(block)}
            </div>
            <textarea
              value={blockContents[block.block_id] ?? ''}
              onChange={(e) => setBlockContents((prev) => ({ ...prev, [block.block_id]: e.target.value }))}
              rows={4}
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-base)',
                lineHeight: 1.6,
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'var(--font-sans)',
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );

  const rightPanel = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--space-3)' }}>
      <div
        style={{
          display: 'flex',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-sm)',
          overflow: 'hidden',
        }}
      >
        <button
          onClick={() => setActiveTab('private')}
          style={{
            flex: 1,
            padding: 'var(--space-2)',
            background: activeTab === 'private' ? 'var(--accent-subtle)' : 'transparent',
            color: activeTab === 'private' ? 'var(--accent)' : 'var(--text-muted)',
            border: 'none',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: activeTab === 'private' ? 600 : 400,
            borderBottom: activeTab === 'private' ? '2px solid var(--accent)' : '2px solid transparent',
          }}
        >
          私域打磨
        </button>
        <button
          onClick={() => setActiveTab('public')}
          style={{
            flex: 1,
            padding: 'var(--space-2)',
            background: activeTab === 'public' ? 'var(--accent-subtle)' : 'transparent',
            color: activeTab === 'public' ? 'var(--accent)' : 'var(--text-muted)',
            border: 'none',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: activeTab === 'public' ? 600 : 400,
            borderBottom: activeTab === 'public' ? '2px solid var(--accent)' : '2px solid transparent',
          }}
        >
          公域博弈
        </button>
      </div>

      {activeTab === 'private' ? (
        <>
          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', display: 'block', marginBottom: 'var(--space-1)' }}>
              AI 角色
            </label>
            <select
              value={aiRolePrivate}
              onChange={(e) => setAiRolePrivate(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-1) var(--space-2)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-sm)',
                outline: 'none',
              }}
            >
              <option value="我的技术顾问">我的技术顾问</option>
              <option value="我的文案助手">我的文案助手</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>信任分</span>
            <div style={{ flex: 1, height: 6, background: 'var(--bg-elevated)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: '50%', height: '100%', background: 'var(--info)', borderRadius: 3 }} />
            </div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--info)', fontWeight: 600 }}>50</span>
          </div>

          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>私有池</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>127/400</span>
          </div>

          <div style={{ flex: 1, overflow: 'auto' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
              提案列表 ({privateProposals.length})
            </div>
            {privateProposals.map((prop) => (
              <ProposalCard key={prop.proposal_id} prop={prop} isPrivate />
            ))}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <input
              type="text"
              placeholder="输入润色指令..."
              value={privateInput}
              onChange={(e) => setPrivateInput(e.target.value)}
              style={{
                flex: 1,
                padding: 'var(--space-2)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-sm)',
                outline: 'none',
              }}
            />
            <button
              style={{
                padding: 'var(--space-2) var(--space-3)',
                background: 'var(--accent)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              请求润色
            </button>
          </div>
        </>
      ) : (
        <>
          <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
            {['TechReviewer', 'LegalAgent'].map((role) => (
              <button
                key={role}
                onClick={() => setAiRolePublic(role)}
                style={{
                  flex: 1,
                  padding: 'var(--space-1) var(--space-2)',
                  background: aiRolePublic === role ? 'var(--accent-subtle)' : 'var(--bg-elevated)',
                  color: aiRolePublic === role ? 'var(--accent)' : 'var(--text-muted)',
                  border: `1px solid ${aiRolePublic === role ? 'var(--accent)' : 'var(--border-default)'}`,
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-xs)',
                  cursor: 'pointer',
                }}
              >
                {role}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>信任分</span>
            <div style={{ flex: 1, height: 6, background: 'var(--bg-elevated)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: '50%', height: '100%', background: 'var(--info)', borderRadius: 3 }} />
            </div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--info)', fontWeight: 600 }}>50</span>
          </div>

          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>公共池</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>643/800</span>
          </div>

          <div
            style={{
              padding: 'var(--space-2)',
              background: 'var(--danger-subtle)',
              border: '1px solid var(--danger)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--text-xs)',
              color: 'var(--danger)',
              textAlign: 'center',
            }}
          >
            ⚠️ 冲突预警: TechReviewer 与 LegalAgent 在 block-003 存在对立提案
          </div>

          <div style={{ flex: 1, overflow: 'auto' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
              提案列表 ({publicProposals.length})
            </div>
            {publicProposals.map((prop) => (
              <ProposalCard key={prop.proposal_id} prop={prop} isPrivate={false} />
            ))}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <input
              type="text"
              placeholder="输入润色指令..."
              value={publicInput}
              onChange={(e) => setPublicInput(e.target.value)}
              style={{
                flex: 1,
                padding: 'var(--space-2)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-sm)',
                outline: 'none',
              }}
            />
            <button
              style={{
                padding: 'var(--space-2) var(--space-3)',
                background: 'var(--accent)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              请求润色
            </button>
          </div>
        </>
      )}
    </div>
  );

  return (
    <ForgeLayout
      leftPanel={leftPanel}
      centerPanel={centerPanel}
      rightPanel={rightPanel}
      onlineCount={3}
      lastSaved="2秒前"
      wordCount={1248}
    />
  );
}

function ProposalCard({ prop, isPrivate }: { prop: ProposalResponse; isPrivate: boolean }) {
  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        borderRadius: 'var(--radius-sm)',
        padding: 'var(--space-3)',
        marginBottom: 'var(--space-2)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: isPrivate ? 'var(--accent)' : 'var(--info)' }}>
          #{prop.proposal_id.slice(-4)}
        </span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          {isPrivate ? prop.block_id : prop.ai_source}
        </span>
      </div>
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 'var(--space-2)' }}>
        {prop.rationale.slice(0, 80)}...
      </p>
      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        <button
          style={{
            flex: 1,
            padding: 'var(--space-1)',
            background: 'var(--success-subtle)',
            color: 'var(--success)',
            border: '1px solid var(--success)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--text-xs)',
            cursor: 'pointer',
          }}
        >
          接受
        </button>
        <button
          style={{
            flex: 1,
            padding: 'var(--space-1)',
            background: 'var(--danger-subtle)',
            color: 'var(--danger)',
            border: '1px solid var(--danger)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--text-xs)',
            cursor: 'pointer',
          }}
        >
          拒绝
        </button>
      </div>
    </div>
  );
}
