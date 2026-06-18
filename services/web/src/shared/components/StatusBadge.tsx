import { DocumentState } from "@/shared/types/contracts";

interface StatusBadgeProps {
  state: DocumentState;
}

const stateConfig: Record<DocumentState, { label: string; color: string; bg: string }> = {
  [DocumentState.DRAFT]: { label: "Draft", color: "var(--info)", bg: "var(--info-bg)" },
  [DocumentState.DISCUSSION]: { label: "Discussion", color: "var(--warning)", bg: "var(--warning-bg)" },
  [DocumentState.REVIEW]: { label: "Review", color: "var(--accent)", bg: "var(--accent-subtle)" },
  [DocumentState.FINALIZED]: { label: "Finalized", color: "var(--success)", bg: "var(--success-bg)" },
  [DocumentState.ARCHIVED]: { label: "Archived", color: "var(--text-muted)", bg: "var(--bg-subtle)" },
};

export function StatusBadge({ state }: StatusBadgeProps) {
  const config = stateConfig[state];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontSize: "var(--text-xs)",
        fontWeight: 600,
        padding: "2px 10px",
        borderRadius: "var(--radius-sm)",
        color: config.color,
        background: config.bg,
        textTransform: "uppercase",
        letterSpacing: "0.03em",
        lineHeight: 1.5,
      }}
    >
      {config.label}
    </span>
  );
}
