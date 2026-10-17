import { type ReactNode, useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

import { Button } from "../button";
import { cn } from "../../lib/cn";
import { dialogStyles as styles } from "./Dialog.styles";

export interface DialogProps {
    open: boolean;
    onClose: () => void;
    title: string;
    description?: string;
    children: ReactNode;
    footer?: ReactNode;
    size?: "sm" | "md" | "lg";
    closeDisabled?: boolean;
    className?: string;
}

export function Dialog({
    open,
    onClose,
    title,
    description,
    children,
    footer,
    size = "md",
    closeDisabled = false,
    className,
}: DialogProps) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const onCloseRef = useRef(onClose);
    const titleId = useId();
    const descriptionId = useId();

    useEffect(() => {
        onCloseRef.current = onClose;
    }, [ onClose ]);

    useEffect(() => {
        const dialog = dialogRef.current;

        if (!dialog) return;

        if (open && !dialog.open) {
            dialog.showModal();
        } else if (!open && dialog.open) {
            dialog.close();
        }
    }, [ open ]);

    function requestClose() {
        if (!closeDisabled) {
            onClose();
        }
    }

    return (
        <dialog
            ref={dialogRef}
            aria-labelledby={titleId}
            aria-describedby={description ? descriptionId : undefined}
            className={cn(styles.root, styles.sizes[size], className)}
            onCancel={(event) => {
                event.preventDefault();
                requestClose();
            }}
            onClick={(event) => {
                if (event.target === event.currentTarget) {
                    requestClose();
                }
            }}
        >
            <div className={styles.content}>
                <div className={styles.header}>
                    <div className={styles.heading}>
                        <h2 id={titleId} className={styles.title}>
                            {title}
                        </h2>

                        {description && (
                            <p id={descriptionId} className={styles.description}>
                                {description}
                            </p>
                        )}
                    </div>

                    <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Close dialog"
                        disabled={closeDisabled}
                        onClick={requestClose}
                    >
                        <X aria-hidden="true"/>
                    </Button>
                </div>

                <div className={styles.body}>
                    {children}
                </div>

                {footer && (
                    <div className={styles.footer}>
                        {footer}
                    </div>
                )}
            </div>
        </dialog>
    );
}
