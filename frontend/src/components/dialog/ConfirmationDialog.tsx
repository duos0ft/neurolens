import { Button } from "../button";
import { Dialog } from "./Dialog";

export interface ConfirmationDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    description: string;
    confirmLabel: string;
    cancelLabel?: string;
    destructive?: boolean;
    loading?: boolean;
}

export function ConfirmationDialog({
    open,
    onClose,
    onConfirm,
    title,
    description,
    confirmLabel,
    cancelLabel = "Cancel",
    destructive = false,
    loading = false,
}: ConfirmationDialogProps) {
    return (
        <Dialog
            open={open}
            onClose={onClose}
            closeDisabled={loading}
            title={title}
            size="md"
            footer={
                <>
                    <Button
                        variant="secondary"
                        disabled={loading}
                        onClick={onClose}
                    >
                        {cancelLabel}
                    </Button>

                    <Button
                        variant={destructive ? "destructive" : "primary"}
                        disabled={loading}
                        onClick={onConfirm}
                    >
                        {loading ? "Please wait..." : confirmLabel}
                    </Button>
                </>
            }
        >
            <p className="text-sm leading-6 text-fg-muted">
                {description}
            </p>
        </Dialog>
    );
}
