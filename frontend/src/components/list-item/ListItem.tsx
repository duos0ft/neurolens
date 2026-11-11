import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";
import { listItemStyles as styles } from "./ListItem.styles";

export interface ListItemProps
    extends Omit<HTMLAttributes<HTMLElement>, "title"> {
    title: ReactNode;
    description?: ReactNode;
    leading?: ReactNode;
    metadata?: ReactNode;
    actions?: ReactNode;
    children?: ReactNode;
    selected?: boolean;
    disabled?: boolean;
}

export function ListItem({
    title,
    description,
    leading,
    metadata,
    actions,
    children,
    selected = false,
    disabled = false,
    className,
    ...props
}: ListItemProps) {
    return (
        <article
            {...props}
            className={cn(
                styles.root,
                selected && styles.selected,
                disabled && styles.disabled,
                className,
            )}
        >
            {leading && (
                <div className={styles.leading}>
                    {leading}
                </div>
            )}

            <div className={styles.content}>
                <div className={styles.heading}>
                    <div className={styles.title}>
                        {title}
                    </div>

                    {actions && (
                        <div className={styles.actions}>
                            {actions}
                        </div>
                    )}
                </div>

                {description && (
                    <div className={styles.description}>
                        {description}
                    </div>
                )}

                {metadata && (
                    <div className={styles.metadata}>
                        {metadata}
                    </div>
                )}

                {children && (
                    <div className={styles.details}>
                        {children}
                    </div>
                )}
            </div>
        </article>
    );
}
