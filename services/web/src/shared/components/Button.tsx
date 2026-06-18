import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "tertiary" | "danger" | "e-stop";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
}

const variantClass: Record<ButtonVariant, string> = {
  primary: "btn btn-primary",
  secondary: "btn btn-secondary",
  tertiary: "btn btn-tertiary",
  danger: "btn btn-danger",
  "e-stop": "btn btn-e-stop",
};

export function Button({
  variant = "primary",
  children,
  className,
  ...props
}: ButtonProps) {
  const cls = `${variantClass[variant]}${className ? " " + className : ""}`;
  return (
    <button className={cls} {...props}>
      {children}
    </button>
  );
}
