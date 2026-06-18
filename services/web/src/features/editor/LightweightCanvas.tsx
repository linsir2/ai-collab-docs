import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useDocumentStore } from '../../shared/store/documentStore';
import type { BlockMetaResponse } from '@/shared/types/contracts';

const MOCK_CONTENTS: Record<string, string> = {
  'block-001': '## 背景与目标\n\n本文档旨在建立一套高效透明的资源调配机制。',
  'block-002': '## 现状分析\n\n当前资源利用率约为78%，存在明显的峰谷波动。',
  'block-003': '## 优化方案\n\n提出三阶段优化策略：第一阶段完成资源池化改造。',
  'block-004': '## 实施路线图\n\n详细的时间表与里程碑。',
  'block-005': '## 预期收益与风险\n\n预期ROI为320%，投资回收期6个月。',
};

export default function LightweightCanvas() {
  const { docId } = useParams<{ docId: string }>();
  const currentDoc = useDocumentStore((s) => s.currentDoc);
  const blockMetas = useDocumentStore((s) => s.blockMetas);
  const fetchDocument = useDocumentStore((s) => s.fetchDocument);
  const fetchBlockMetas = useDocumentStore((s) => s.fetchBlockMetas);

  const [showAI, setShowAI] = useState(false);
  const [blockContents, setBlockContents] = useState<Record<string, string>>({});
  const [focusedBlock, setFocusedBlock] = useState<string | null>(null);
  const [aiInput, setAiInput] = useState('');
  const [aiSuggestions] = useState([
    '建议在开头增加背景说明段落',
    '简化第二段的表述，使其更加精炼',
    '核心论点的支撑材料需要加强',
  ]);

  useEffect(() => {
    if (docId) {
      fetchDocument(docId);
      fetchBlockMetas(docId);
    }
  }, [docId, fetchDocument, fetchBlockMetas]);

  useEffect(() => {
    if (blockMetas.length > 0) {
      const contents: Record<string, string> = {};
      for (const b of blockMetas) {
        contents[b.block_id] = MOCK_CONTENTS[b.block_id] ?? '(内容加载中...)';
      }
      setBlockContents(contents);
    }
  }, [blockMetas]);

  const getBlockBorderStyle = (block: BlockMetaResponse): React.CSSProperties => {
    const tags = block.tags as string[];
    if (tags.includes('locked-by-human')) {
      return { borderLeft: '2px solid var(--danger)' };
    }
    if (tags.includes('drift-warning')) {
      return { borderLeft: '2px dashed var(--warning)' };
    }
    if (tags.includes('claimed')) {
      return { borderLeft: '2px dotted var(--info)' };
    }
    return { borderLeft: '2px solid var(--border-subtle)' };
  };

  const getBlockTag = (block: BlockMetaResponse) => {
    const tags = block.tags as string[];
    if (tags.includes('locked-by-human')) {
      return (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--danger)', background: 'var(--danger-subtle)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>
          LOCK
        </span>
      );
    }
    if (tags.includes('drift-warning')) {
      return (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--warning)', background: 'var(--warning-subtle)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>
          WARN
        </span>
      );
    }
    return null;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--space-6)',
          padding: 'var(--space-2) var(--space-4)',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-default)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)' }} />
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', fontWeight: 600 }}>创作中</span>
        </div>
        <span style={{ color: 'var(--text-muted)' }}>→</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--border-default)' }} />
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>已定稿</span>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 'var(--space-6)', maxWidth: 800, margin: '0 auto', width: '100%' }}>
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, marginBottom: 'var(--space-2)' }}>
            {currentDoc?.title || '加载中...'}
          </h2>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
            {currentDoc?.anchor_statement}
          </p>
        </div>

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

      <div
        style={{
          height: 28,
          minHeight: 28,
          background: 'var(--bg-subtle)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 var(--space-4)',
          fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)',
          justifyContent: 'space-between',
        }}
      >
        <span>创作中</span>
        <span>字数 1,248</span>
      </div>

      <button
        onClick={() => setShowAI(!showAI)}
        style={{
          position: 'fixed',
          bottom: 48,
          right: 20,
          width: 40,
          height: 40,
          borderRadius: '50%',
          background: 'var(--accent)',
          border: 'none',
          color: '#fff',
          fontSize: 20,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px var(--accent-glow)',
          zIndex: 100,
          transition: 'transform 0.15s',
        }}
      >
        AI
      </button>

      {showAI && (
        <div
          style={{
            position: 'fixed',
            bottom: 100,
            right: 20,
            width: 360,
            maxHeight: 480,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 100,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: 'var(--space-3)',
              borderBottom: '1px solid var(--border-default)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              我的文案助手
            </span>
            <button
              onClick={() => setShowAI(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: 16,
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ flex: 1, overflow: 'auto', padding: 'var(--space-3)' }}>
            {aiSuggestions.map((s, i) => (
              <div
                key={i}
                style={{
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'var(--bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: 'var(--space-2)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-secondary)',
                  borderLeft: '2px solid var(--accent)',
                }}
              >
                {s}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-2)', padding: 'var(--space-3)', borderTop: '1px solid var(--border-default)' }}>
            <input
              type="text"
              placeholder="输入你的问题..."
              value={aiInput}
              onChange={(e) => setAiInput(e.target.value)}
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
                cursor: 'pointer',
              }}
            >
              发送
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
