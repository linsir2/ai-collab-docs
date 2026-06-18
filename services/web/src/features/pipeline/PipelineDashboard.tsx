import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentStore } from '../../shared/store/documentStore';
import { DocumentState } from '../../shared/types';
import { STATE_LABELS, STATE_ORDER, ALLOWED_TRANSITIONS } from '../../shared/types';

export default function PipelineDashboard() {
  const documents = useDocumentStore((s) => s.documents);
  const fetchDocuments = useDocumentStore((s) => s.fetchDocuments);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const groupedByState = useMemo(() => {
    const groups: Record<string, typeof documents> = {};
    for (const state of STATE_ORDER) {
      groups[state] = [];
    }
    for (const doc of documents) {
      if (groups[doc.state]) {
        groups[doc.state].push(doc);
      }
    }
    return groups;
  }, [documents]);

  const totalProposals = 643;
  const maxProposals = 800;
  const saturationPercent = Math.round((totalProposals / maxProposals) * 100);

  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
    } catch {
      return '';
    }
  };

  const getNextState = (state: DocumentState): string | null => {
    const transitions = ALLOWED_TRANSITIONS[state];
    if (transitions && transitions.length > 0) {
      return transitions[0];
    }
    return null;
  };

  return (
    <div style={{ padding: 'var(--space-6)', height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 600 }}>生产流水线控制大盘</h1>
        <button
          onClick={() => navigate('/documents/new')}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'opacity 0.15s',
          }}
        >
          新建文档 [+]
        </button>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          padding: 'var(--space-3) var(--space-4)',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', minWidth: 100 }}>
          Token 饱和度
        </span>
        <div style={{ flex: 1, height: 10, background: 'var(--bg-elevated)', borderRadius: 5, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${saturationPercent}%`,
              background: `linear-gradient(90deg, var(--warning), var(--danger))`,
              borderRadius: 5,
              transition: 'width 0.5s',
            }}
          />
        </div>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--warning)', fontWeight: 600, minWidth: 50, textAlign: 'right' }}>
          {saturationPercent}%
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
          padding: 'var(--space-3) var(--space-4)',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>提案池</span>
        <span style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text-primary)' }}>
          {totalProposals}
        </span>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>/ {maxProposals}</span>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          文档总数: {documents.length}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-3)', minHeight: 0, flex: 1 }}>
        {STATE_ORDER.map((state) => {
          const docs = groupedByState[state] ?? [];
          return (
            <div
              key={state}
              style={{
                flex: 1,
                minWidth: 180,
                background: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  padding: 'var(--space-2) var(--space-3)',
                  borderBottom: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {STATE_LABELS[state]}
                </span>
                <span
                  style={{
                    fontSize: 'var(--text-xs)',
                    background: 'var(--bg-elevated)',
                    color: 'var(--text-muted)',
                    padding: '1px 8px',
                    borderRadius: 10,
                  }}
                >
                  {docs.length}
                </span>
              </div>

              <div style={{ flex: 1, overflow: 'auto', padding: 'var(--space-2)' }}>
                {docs.length === 0 && (
                  <div style={{ padding: 'var(--space-4)', textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                    暂无文档
                  </div>
                )}
                {docs.map((doc) => {
                  const nextState = getNextState(doc.state as DocumentState);
                  return (
                    <div
                      key={doc.doc_id}
                      style={{
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--space-3)',
                        marginBottom: 'var(--space-2)',
                        cursor: 'pointer',
                        transition: 'border-color 0.15s',
                      }}
                      onClick={() => navigate(`/documents/${doc.doc_id}/forge`)}
                    >
                      <div style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
                        {doc.title}
                      </div>
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
                        {doc.owner_id} · {formatTime(doc.updated_at)}
                      </div>
                      {nextState && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                          }}
                          style={{
                            width: '100%',
                            padding: 'var(--space-1) 0',
                            background: 'var(--accent-subtle)',
                            color: 'var(--accent)',
                            border: '1px solid var(--accent)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 'var(--text-xs)',
                            cursor: 'pointer',
                            textAlign: 'center',
                            transition: 'opacity 0.15s',
                          }}
                        >
                          下一状态: {STATE_LABELS[nextState]}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
