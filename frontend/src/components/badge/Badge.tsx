import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";
import { badgeStyles as styles } from "./Badge.styles";

export type BadgeVariant =
    | "neutral"
    | "success"
    | "warning"
    | "danger";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    children: ReactNode;
    variant?: BadgeVariant;
}

export function Badge({
    children,
    variant = "neutral",
    className,
    ...props
}: BadgeProps) {
    return (
        <span
            className={cn(
                styles.root,
                styles.variants[variant],
                className,
            )}
            {...props}
        >
            {children}
        </span>
    );
}
