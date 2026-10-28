import { useState } from "react";
import { toast } from "sonner";

import { ConfirmationDialog } from "../dialog/ConfirmationDialog";
import { DropdownMenu } from "../dropdown-menu/DropdownMenu";

import type { TableRowAction } from "./Table";

interface TableRowActionsProps<T> {
    row: T;
    actions: TableRowAction<T>[];
    onSuccess?: (row: T, action: TableRowAction<T>) => void | Promise<void>;
    onError?: (error: unknown, row: T, action: TableRowAction<T>) => void;
}

export function TableRowActions<T>({
    row,
    actions,
    onSuccess,
    onError,
}: TableRowActionsProps<T>) {
    const [ selectedAction, setSelectedAction ] =
        useState<TableRowAction<T> | null>(null);

    const [ pending, setPending ] = useState(false);

    const availableActions = actions.filter(
        (action) => !action.hidden?.(row),
    );

    async function executeAction(action: TableRowAction<T>) {
        if (pending) {
            return;
        }

        setPending(true);

        try {
            await action.onSelect(row);

            setSelectedAction(null);

            if (onSuccess) {
                await onSuccess(row, action);
            }
        } catch (error) {
            if (onError) {
                onError(error, row, action);
            } else {
                toast.error("Unable to complete this action. Please try again.");
            }
        } finally {
            setPending(false);
        }
    }

    function selectAction(action: TableRowAction<T>) {
        if (pending || action.disabled?.(row)) {
            return;
        }

        if (action.confirmation) {
            setSelectedAction(action);
        } else {
            void executeAction(action);
        }
    }

    if (availableActions.length === 0) {
        return null;
    }

    const confirmation = selectedAction?.confirmation;

    const description = confirmation
        ? typeof confirmation.description === "function"
            ? confirmation.description(row)
            : confirmation.description
        : "";

    return (
        <>
            <DropdownMenu
                label="Row actions"
                disabled={pending}
                items={availableActions.map((action) => {
                    const Icon = action.icon;

                    return {
                        label: action.label,
                        icon: Icon ? <Icon className="size-4"/> : undefined,
                        destructive: action.destructive,
                        disabled: action.disabled?.(row),
                        onSelect: () => selectAction(action),
                    };
                })}
            />

            <ConfirmationDialog
                open={selectedAction !== null}
                onClose={() => {
                    if (!pending) {
                        setSelectedAction(null);
                    }
                }}
                onConfirm={() => {
                    if (selectedAction) {
                        void executeAction(selectedAction);
                    }
                }}
                loading={pending}
                destructive={selectedAction?.destructive}
                title={confirmation?.title ?? ""}
                description={description}
                confirmLabel={confirmation?.confirmLabel ?? ""}
            />
        </>
    );
}
