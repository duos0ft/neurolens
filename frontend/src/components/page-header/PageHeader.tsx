import type { ReactNode } from "react";

import { cn } from "../../lib/cn";
import { pageHeaderStyles as styles } from "./PageHeader.styles";

export interface PageHeaderProps {
    title: string;
    description?: string;
    actions?: ReactNode;
    className?: string;
}

export function PageHeader({
    title,
    description,
    actions,
    className,
}: PageHeaderProps) {
    return (
        <header className={cn(styles.root, className)}>
            <div className={styles.content}>
                <h1 className={styles.title}>{title}</h1>

                {description && (
                    <p className={styles.description}>
                        {description}
                    </p>
                )}
            </div>

            {actions && (
                <div className={styles.actions}>
                    {actions}
                </div>
            )}
        </header>
    );
}
