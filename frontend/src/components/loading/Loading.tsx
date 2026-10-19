import type { HTMLAttributes } from "react";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../../lib/cn";

import { loadingStyles as styles } from "./Loading.styles";

interface LoadingProps
    extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof styles.spinner> {
    title?: string;
    description?: string;
    fullscreen?: boolean;
}

export function Loading({
    size = "md",
    title,
    description,
    fullscreen = false,
    className,
    ...props
}: LoadingProps) {
    return (
        <div
            role="status"
            aria-live="polite"
            aria-label={title ?? "Loading"}
            className={cn(
                styles.root,
                fullscreen && styles.fullscreen,
                className,
            )}
            {...props}
        >
            <div
                aria-hidden="true"
                className={styles.spinner({ size })}
            />

            {(title || description) && (
                <div className={styles.content}>
                    {title && (
                        <p className={styles.title}>
                            {title}
                        </p>
                    )}

                    {description && (
                        <p className={styles.description}>
                            {description}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
