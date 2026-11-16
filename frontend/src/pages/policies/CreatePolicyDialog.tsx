import { useMutation } from "@tanstack/react-query";
import { type SubmitEvent, useId, useState } from "react";
import { toast } from "sonner";

import { Button } from "../../components/button";
import { Dialog } from "../../components/dialog";
import { Input } from "../../components/input";
import { Select } from "../../components/select/Select";
import type { SelectOption } from "../../components/select/Select.types";
import { createPolicyDocument, type PolicyCategory, type PolicyDocument } from "../../lib/policies";
import { createPolicyDialogStyles as styles } from "./CreatePolicyDialog.styles";

interface CreatePolicyDialogProps {
    open: boolean;
    onClose: () => void;
    onCreated: (policy: PolicyDocument) => void;
}

const categoryOptions: SelectOption<PolicyCategory>[] = [
    { label: "Leave", value: "leave" },
    { label: "Remote work", value: "remote_work" },
    { label: "Working hours", value: "working_hours" },
    { label: "Communication", value: "communication" },
    { label: "Accessibility", value: "accessibility" },
    { label: "Information security", value: "information_security" },
    { label: "Other", value: "other" },
];

export function CreatePolicyDialog({
    open,
    onClose,
    onCreated,
}: CreatePolicyDialogProps) {
    const formId = useId();
    const titleId = useId();
    const descriptionId = useId();

    const [ title, setTitle ] = useState("");
    const [ description, setDescription ] = useState("");
    const [ category, setCategory ] = useState<PolicyCategory>("other");
    const [ validationError, setValidationError ] = useState<string | null>(null);

    const createMutation = useMutation({
        mutationFn: createPolicyDocument,
    });

    function closeDialog() {
        if (createMutation.isPending) {
            return;
        }

        setTitle("");
        setDescription("");
        setCategory("other");
        setValidationError(null);
        createMutation.reset();
        onClose();
    }

    async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();

        if (createMutation.isPending) {
            return;
        }

        const normalizedTitle = title.trim().replace(/\s+/g, " ");
        const normalizedDescription = description.trim() || null;

        if (!normalizedTitle || normalizedTitle.length > 200) {
            setValidationError(
                "Policy title must contain between 1 and 200 characters.",
            );
            return;
        }

        if (normalizedDescription && normalizedDescription.length > 2000) {
            setValidationError(
                "Description cannot exceed 2000 characters.",
            );
            return;
        }

        setValidationError(null);

        try {
            const policy = await createMutation.mutateAsync({
                title: normalizedTitle,
                description: normalizedDescription,
                category,
            });

            toast.success("Policy created successfully.", {
                description: "Upload a PDF version to prepare the policy for publishing.",
            });

            onCreated(policy);
            closeDialog();
        } catch (error) {
            toast.error("Unable to create policy.", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        }
    }

    const isValid = Boolean(
        title.trim()
        && title.trim().length <= 200
        && description.trim().length <= 2000,
    );

    return (
        <Dialog
            open={open}
            onClose={closeDialog}
            closeDisabled={createMutation.isPending}
            title="New policy"
            description="Create a company policy that can later be uploaded and published to the knowledge base."
            size="md"
            footer={
                <>
                    <Button
                        type="button"
                        variant="secondary"
                        disabled={createMutation.isPending}
                        onClick={closeDialog}
                    >
                        Cancel
                    </Button>

                    <Button
                        type="submit"
                        form={formId}
                        variant="primary"
                        disabled={createMutation.isPending || !isValid}
                    >
                        {createMutation.isPending
                            ? "Creating..."
                            : "Create policy"}
                    </Button>
                </>
            }
        >
            <form
                id={formId}
                className={styles.form}
                onSubmit={(event) => void handleSubmit(event)}
                noValidate
            >
                {validationError && (
                    <p className={styles.error} role="alert">
                        {validationError}
                    </p>
                )}

                <div className={styles.field}>
                    <label htmlFor={titleId} className={styles.label}>
                        Policy title
                    </label>

                    <Input
                        id={titleId}
                        value={title}
                        onChange={(event) => {
                            setTitle(event.target.value);
                            setValidationError(null);
                        }}
                        placeholder="e.g. Annual Leave Policy"
                        maxLength={200}
                        required
                        disabled={createMutation.isPending}
                    />
                </div>

                <div className={styles.field}>
                    <label className={styles.label}>
                        Category
                    </label>

                    <Select<PolicyCategory>
                        options={categoryOptions}
                        value={category}
                        onChange={(value) => {
                            if (value !== null) {
                                setCategory(value);
                            }
                        }}
                        placeholder="Select category"
                        disabled={createMutation.isPending}
                    />

                    <p className={styles.hint}>
                        Helps organize policies in the company knowledge base.
                    </p>
                </div>

                <div className={styles.field}>
                    <label htmlFor={descriptionId} className={styles.label}>
                        Description
                    </label>

                    <textarea
                        id={descriptionId}
                        className={styles.textarea}
                        value={description}
                        onChange={(event) => {
                            setDescription(event.target.value);
                            setValidationError(null);
                        }}
                        placeholder="Briefly describe what this policy covers..."
                        rows={3}
                        maxLength={2000}
                        disabled={createMutation.isPending}
                    />

                    <p className={styles.hint}>
                        Optional. This description is for administrators;
                        the uploaded policy will provide the actual source content.
                    </p>
                </div>
            </form>
        </Dialog>
    );
}
