import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentStore } from '../../shared/store/documentStore';

const DOC_TYPES = ['技术方案', '商业BP', '合规报告', '公文', '合同草案'];

export default function ForgeInitiation() {
  const createDocument = useDocumentStore((s) => s.createDocument);
  const navigate = useNavigate();

  const [statement, setStatement] = useState('');
  const [docType, setDocType] = useState('技术方案');
  const [collaborationMode, setCollaborationMode] = useState<'heavy' | 'light'>('heavy');
  const [title, setTitle] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [coreArgument, setCoreArgument] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isStatementValid = statement.length >= 20;
  const isTitleValid = title.trim().length > 0;
  const canSubmit = isStatementValid && isTitleValid && !isSubmitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setError('');
    setIsSubmitting(true);
    try {
      const doc = await createDocument({
        title: title.trim(),
        anchor_statement: statement.trim(),
        anchor_audience: targetAudience.trim(),
        anchor_argument: coreArgument.trim(),
      });
      if (collaborationMode === 'light') {
        navigate(`/documents/${doc.doc_id}/forge/light`);
      } else {
        navigate(`/documents/${doc.doc_id}/forge`);
      }
    } catch {
      setError('创建文档失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: 'var(--space-2) var(--space-3)',
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    fontSize: 'var(--text-base)',
    outline: 'none',
    transition: 'border-color 0.15s',
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-8)',
        minHeight: '100%',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 560,
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-default)',
          padding: 'var(--space-8)',
        }}
      >
        <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, marginBottom: 'var(--space-6)' }}>
          开始锻造
        </h2>

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label
            style={{
              display: 'block',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            立意主旨描述 *
          </label>
          <textarea
            rows={3}
            placeholder="描述你想要锻造的文档核心目标..."
            value={statement}
            onChange={(e) => setStatement(e.target.value)}
            style={{ ...inputStyle, resize: 'vertical', minHeight: 60 }}
          />
          <div
            style={{
              fontSize: 'var(--text-xs)',
              color: isStatementValid ? 'var(--success)' : 'var(--text-muted)',
              marginTop: 'var(--space-1)',
            }}
          >
            {statement.length}/20 字
          </div>
        </div>

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label
            style={{
              display: 'block',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            文档标题 *
          </label>
          <input
            type="text"
            placeholder="输入文档标题"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label
            style={{
              display: 'block',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            文档类型
          </label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            style={inputStyle}
          >
            {DOC_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label
            style={{
              display: 'block',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            协作模式
          </label>
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            {(['heavy', 'light'] as const).map((mode) => (
              <label
                key={mode}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  padding: 'var(--space-2) var(--space-3)',
                  background: collaborationMode === mode ? 'var(--accent-subtle)' : 'var(--bg-surface)',
                  border: `1px solid ${collaborationMode === mode ? 'var(--accent)' : 'var(--border-default)'}`,
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-primary)',
                  transition: 'all 0.15s',
                }}
              >
                <input
                  type="radio"
                  name="mode"
                  value={mode}
                  checked={collaborationMode === mode}
                  onChange={() => setCollaborationMode(mode)}
                  style={{ accentColor: 'var(--accent)' }}
                />
                {mode === 'heavy' ? '重型锻造模式' : '轻量创作模式'}
              </label>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label
            style={{
              display: 'block',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            目标读者
          </label>
          <input
            type="text"
            placeholder="目标读者群体"
            value={targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label
            style={{
              display: 'block',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            核心论点
          </label>
          <textarea
            rows={2}
            placeholder="文档的核心论点"
            value={coreArgument}
            onChange={(e) => setCoreArgument(e.target.value)}
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </div>

        {error && (
          <div
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: 'var(--danger-subtle)',
              border: '1px solid var(--danger)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--danger)',
              fontSize: 'var(--text-sm)',
              marginBottom: 'var(--space-4)',
            }}
          >
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          style={{
            width: '100%',
            padding: 'var(--space-3) 0',
            background: canSubmit ? 'var(--accent)' : 'var(--bg-surface)',
            color: canSubmit ? '#fff' : 'var(--text-muted)',
            border: canSubmit ? 'none' : '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--text-base)',
            fontWeight: 600,
            cursor: canSubmit ? 'pointer' : 'not-allowed',
            transition: 'all 0.15s',
          }}
        >
          {isSubmitting ? '创建中...' : '开始锻造'}
        </button>
      </div>
    </div>
  );
}
