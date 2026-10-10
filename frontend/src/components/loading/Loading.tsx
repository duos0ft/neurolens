import type { HTMLAttributes } from "react";
import type { VariantProps } from "class-variance-authority";
import { loadingStyles as styles } from "./Loading.styles";
import { cn } from "../../lib/cn";

interface LoadingProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof styles.spinner> {
    title?: string;
    description?: string;
}

export function Loading({ size = "md", title, description, className, ...props }: LoadingProps) {
    return (
        <div
            role="status"
            aria-live="polite"
            aria-label={title ?? "Loading"}
            className={cn(styles.root, className)}
            {...props}
        >
            <div aria-hidden="true" className={styles.spinner({ size })} />

            {(title || description) && (
                <div className={styles.content}>
                    {title && <p className={styles.title}>{title}</p>}
                    {description && <p className={styles.description}>{description}</p>}
                </div>
            )}
        </div>
    );
}
