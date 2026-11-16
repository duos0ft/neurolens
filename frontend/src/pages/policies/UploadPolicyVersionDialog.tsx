import { useMutation } from "@tanstack/react-query";
import { type SubmitEvent, useId, useState } from "react";
import { toast } from "sonner";

import { Button } from "../../components/button";
import { DatePicker } from "../../components/date-picker/DatePicker";
import { Dialog } from "../../components/dialog";
import { type PolicyDocument, uploadPolicyVersion } from "../../lib/policies";
import { uploadPolicyVersionDialogStyles as styles } from "./UploadPolicyVersionDialog.styles";

interface UploadPolicyVersionDialogProps {
    open: boolean;
    policy: PolicyDocument;
    onClose: () => void;
    onUploaded: () => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export function UploadPolicyVersionDialog({
    open,
    policy,
    onClose,
    onUploaded,
}: UploadPolicyVersionDialogProps) {
    const formId = useId();
    const fileId = useId();

    const [ file, setFile ] = useState<File | null>(null);
    const [ effectiveDate, setEffectiveDate ] = useState<string | null>(null);
    const [ validationError, setValidationError ] = useState<string | null>(null);

    const uploadMutation = useMutation({
        mutationFn: uploadPolicyVersion,
    });

    function closeDialog() {
        if (uploadMutation.isPending) {
            return;
        }

        setFile(null);
        setEffectiveDate(null);
        setValidationError(null);
        uploadMutation.reset();
        onClose();
    }

    function handleFileChange(
        event: React.ChangeEvent<HTMLInputElement>,
    ) {
        const selectedFile = event.target.files?.[0] ?? null;

        setValidationError(null);

        if (!selectedFile) {
            setFile(null);
            return;
        }

        if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
            setFile(null);
            setValidationError("Please select a PDF file.");
            return;
        }

        if (selectedFile.size === 0 || selectedFile.size > MAX_FILE_SIZE) {
            setFile(null);
            setValidationError(
                "PDF files must be larger than 0 bytes and no more than 10 MB.",
            );
            return;
        }

        setFile(selectedFile);
    }

    async function handleSubmit(
        event: SubmitEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        if (!file || uploadMutation.isPending) {
            return;
        }

        try {
            await uploadMutation.mutateAsync({
                documentId: policy.id,
                file,
                effectiveDate,
            });

            toast.success("Policy PDF uploaded successfully.", {
                description: "The new version is a draft and is pending processing.",
            });

            onUploaded();
            closeDialog();
        } catch (error) {
            toast.error("Unable to upload policy PDF.", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        }
    }

    return (
        <Dialog
            open={open}
            onClose={closeDialog}
            closeDisabled={uploadMutation.isPending}
            title="Upload policy PDF"
            description={`Upload a new document version for ${policy.title}.`}
            size="md"
            footer={
                <>
                    <Button
                        type="button"
                        variant="secondary"
                        disabled={uploadMutation.isPending}
                        onClick={closeDialog}
                    >
                        Cancel
                    </Button>

                    <Button
                        type="submit"
                        form={formId}
                        variant="primary"
                        disabled={!file || uploadMutation.isPending}
                    >
                        {uploadMutation.isPending
                            ? "Uploading..."
                            : "Upload PDF"}
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
                    <label htmlFor={fileId} className={styles.label}>
                        PDF document
                    </label>

                    <input
                        id={fileId}
                        type="file"
                        accept=".pdf,application/pdf"
                        className={styles.fileInput}
                        onChange={handleFileChange}
                        disabled={uploadMutation.isPending}
                        required
                    />

                    {file && (
                        <p className={styles.fileDetails}>
                            {file.name}
                            {" · "}
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                    )}

                    <p className={styles.hint}>
                        Maximum file size: 10 MB. Only PDF documents
                        are supported.
                    </p>
                </div>

                <div className={styles.field}>
                    <label className={styles.label}>
                        Effective date
                    </label>

                    <DatePicker
                        value={effectiveDate}
                        onChange={setEffectiveDate}
                        disabled={uploadMutation.isPending}
                        clearable
                    />

                    <p className={styles.hint}>
                        Optional. The date from which this policy version
                        takes effect.
                    </p>
                </div>
            </form>
        </Dialog>
    );
}
