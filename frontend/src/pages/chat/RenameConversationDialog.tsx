import { type SyntheticEvent, useEffect, useState } from "react";

import { Button } from "../../components/button";
import { Dialog } from "../../components/dialog";
import { Input } from "../../components/input";
import { chatPageStyles as styles } from "./ChatPage.styles";

interface RenameConversationDialogProps {
    open: boolean;
    title: string;
    loading: boolean;
    onClose: () => void;
    onSave: (title: string) => void;
}

export function RenameConversationDialog({
    open,
    title,
    loading,
    onClose,
    onSave,
}: RenameConversationDialogProps) {
    const [ value, setValue ] = useState(title);

    useEffect(() => {
        if (open) {
            setValue(title);
        }
    }, [ open, title ]);

    function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault();

        const normalized = value.trim().replace(/\s+/g, " ");

        if (!normalized || normalized.length > 100 || loading) {
            return;
        }

        onSave(normalized);
    }

    const normalized = value.trim().replace(/\s+/g, " ");

    return (
        <Dialog
            open={open}
            onClose={onClose}
            title="Rename conversation"
            description="Choose a name that makes this conversation easy to recognize."
            size="sm"
            closeDisabled={loading}
            footer={
                <>
                    <Button
                        variant="secondary"
                        disabled={loading}
                        onClick={onClose}
                    >
                        Cancel
                    </Button>

                    <Button
                        variant="primary"
                        type="submit"
                        form="rename-conversation-form"
                        disabled={!normalized || normalized.length > 100 || loading}
                    >
                        {loading ? "Saving..." : "Save name"}
                    </Button>
                </>
            }
        >
            <form
                id="rename-conversation-form"
                onSubmit={handleSubmit}
                className={styles.renameForm}
            >
                <label
                    htmlFor="rename-conversation-title"
                    className={styles.renameLabel}
                >
                    Conversation name
                </label>

                <Input
                    id="rename-conversation-title"
                    value={value}
                    onChange={(event) => setValue(event.target.value)}
                    placeholder="e.g. Preparing for a meeting"
                    maxLength={100}
                    disabled={loading}
                    autoFocus
                />
            </form>
        </Dialog>
    );
}
