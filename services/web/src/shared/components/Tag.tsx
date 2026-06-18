import type { ReactNode } from "react";

type TagVariant = "locked" | "warning" | "claimed" | "success" | "default";

interface TagProps {
  variant?: TagVariant;
  children: ReactNode;
}

const tagClass: Record<TagVariant, string> = {
  locked: "tag tag-locked",
  warning: "tag tag-warning",
  claimed: "tag tag-claimed",
  success: "tag tag-success",
  default: "tag",
};

export function Tag({ variant = "default", children }: TagProps) {
  return <span className={tagClass[variant]}>{children}</span>;
}
