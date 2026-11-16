import { useId, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, FileText, RefreshCw, Upload } from "lucide-react";

import { Button } from "../../components/button";
import { Dialog } from "../../components/dialog";
import { toast } from "../../components/toast";
import {
    getPolicyVersionFileUrl,
    getPolicyVersions,
    type PolicyDocument,
    type PolicyVersion,
    publishPolicyVersion,
} from "../../lib/policies";
import { UploadPolicyVersionForm } from "./UploadPolicyVersionForm";
import { policyDetailsDialogStyles as styles } from "./PolicyDetailsDialog.styles";

interface PolicyDetailsDialogProps {
    policy: PolicyDocument | null;
    onClose: () => void;
}

type DialogView = "details" | "upload" | "confirmPublish";

function formatDate(value: string): string {
    return new Date(value).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function formatStatus(version: PolicyVersion): string {
    if (version.publication_status === "published") {
        return "Published";
    }

    if (version.publication_status === "archived") {
        return "Archived";
    }

    switch (version.ingestion_status) {
        case "pending":
            return "Waiting to process";
        case "processing":
            return "Processing document...";
        case "ready":
            return "Ready to publish";
        case "failed":
            return "Processing failed";
    }
}

export function PolicyDetailsDialog({
    policy,
    onClose,
}: PolicyDetailsDialogProps) {
    const queryClient = useQueryClient();
    const uploadFormId = useId();

    const [ view, setView ] = useState<DialogView>("details");
    const [ uploadPending, setUploadPending ] = useState(false);
    const [ versionToPublish, setVersionToPublish ] = useState<string | null>(null);

    const documentId = policy?.id;

    const versionsQuery = useQuery({
        queryKey: [ "admin", "policies", documentId, "versions" ],
        queryFn: () => getPolicyVersions(documentId!),
        enabled: Boolean(documentId),
        refetchInterval: (query) => {
            const versions = query.state.data?.versions;

            const isProcessing = versions?.some(
                (version) =>
                    version.ingestion_status === "pending"
                    || version.ingestion_status === "processing",
            );

            return isProcessing ? 3_000 : false;
        },
    });

    const publishMutation = useMutation({
        mutationFn: (versionId: string) => {
            if (!documentId) {
                throw new Error("No policy selected");
            }

            return publishPolicyVersion(documentId, versionId);
        },
        onSuccess: async () => {
            setVersionToPublish(null);
            setView("details");

            await Promise.all([
                queryClient.invalidateQueries({
                    queryKey: [ "admin", "policies", documentId, "versions" ],
                }),
                queryClient.invalidateQueries({
                    queryKey: [ "admin", "policies" ],
                }),
                queryClient.invalidateQueries({
                    queryKey: [ "policies", "published" ],
                }),
            ]);

            toast.success("Policy published successfully.");
        },
        onError: (error) => {
            toast.error("Unable to publish policy.", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const versions = versionsQuery.data?.versions ?? [];

    const publishedVersion = versions.find(
        (version) => version.publication_status === "published",
    );

    const pendingPublication = versions.find(
        (version) => version.id === versionToPublish,
    );

    const busy = uploadPending || publishMutation.isPending;

    function handleClose() {
        if (busy) {
            return;
        }

        setView("details");
        setVersionToPublish(null);
        onClose();
    }

    function handleBack() {
        if (busy) {
            return;
        }

        setView("details");
        setVersionToPublish(null);
    }

    function handleUploaded() {
        setView("details");

        if (documentId) {
            void queryClient.invalidateQueries({
                queryKey: [ "admin", "policies", documentId, "versions" ],
            });
        }
    }

    function handlePublish(version: PolicyVersion) {
        if (busy) {
            return;
        }

        if (publishedVersion && publishedVersion.id !== version.id) {
            setVersionToPublish(version.id);
            setView("confirmPublish");
            return;
        }

        publishMutation.mutate(version.id);
    }

    function confirmPublication() {
        if (!versionToPublish || busy) {
            return;
        }

        publishMutation.mutate(versionToPublish);
    }

    if (!policy) {
        return null;
    }

    const dialogTitle = view === "upload"
        ? "Upload policy PDF"
        : view === "confirmPublish"
            ? "Publish new policy version?"
            : policy.title;

    const dialogDescription = view === "upload"
        ? `Upload a new document version for ${policy.title}.`
        : view === "details"
            ? "Review policy details and uploaded document versions."
            : undefined;

    return (
        <Dialog
            open
            onClose={handleClose}
            closeDisabled={busy}
            title={dialogTitle}
            description={dialogDescription}
            size="lg"
            footer={
                view === "details" ? (
                    <Button
                        type="button"
                        variant="secondary"
                        disabled={busy}
                        onClick={handleClose}
                    >
                        Close
                    </Button>
                ) : view === "upload" ? (
                    <>
                        <Button
                            type="button"
                            variant="secondary"
                            disabled={busy}
                            onClick={handleBack}
                        >
                            Cancel
                        </Button>

                        <Button
                            type="submit"
                            form={uploadFormId}
                            variant="primary"
                            disabled={busy}
                        >
                            {uploadPending ? "Uploading..." : "Upload PDF"}
                        </Button>
                    </>
                ) : (
                    <>
                        <Button
                            type="button"
                            variant="secondary"
                            disabled={busy || !pendingPublication}
                            onClick={handleBack}
                        >
                            Cancel
                        </Button>

                        <Button
                            type="button"
                            variant="primary"
                            disabled={busy || !pendingPublication}
                            onClick={confirmPublication}
                        >
                            {publishMutation.isPending
                                ? "Publishing..."
                                : "Publish version"}
                        </Button>
                    </>
                )
            }
        >
            {view === "upload" ? (
                <div className={styles.content}>
                    <div>
                        <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            disabled={busy}
                            onClick={handleBack}
                        >
                            <ArrowLeft/>
                            Back to policy
                        </Button>
                    </div>

                    <UploadPolicyVersionForm
                        key={policy.id}
                        documentId={policy.id}
                        formId={uploadFormId}
                        onPendingChange={setUploadPending}
                        onUploaded={handleUploaded}
                    />
                </div>
            ) : view === "confirmPublish" ? (
                <div className={styles.content}>
                    <p className={styles.description}>
                        Publishing version {pendingPublication?.version_number} of{" "}
                        <strong>{policy.title}</strong> will archive the currently
                        published version {publishedVersion?.version_number}.
                    </p>

                    <p className={styles.versionMeta}>
                        The previous version will remain in the policy history.
                        Employees will see the newly published version once its
                        effective date has arrived.
                    </p>
                </div>
            ) : (
                <div className={styles.content}>
                    {policy.description && (
                        <p className={styles.description}>
                            {policy.description}
                        </p>
                    )}

                    <div className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h3 className={styles.sectionTitle}>
                                Document versions
                            </h3>

                            <Button
                                type="button"
                                variant="secondary"
                                size="sm"
                                disabled={busy}
                                onClick={() => setView("upload")}
                            >
                                <Upload/>
                                Upload PDF
                            </Button>
                        </div>

                        {versionsQuery.isPending ? (
                            <p className={styles.versionMeta}>
                                Loading versions...
                            </p>
                        ) : versionsQuery.isError ? (
                            <div className={styles.section}>
                                <p className={styles.error} role="alert">
                                    Unable to load policy versions.
                                </p>

                                <div>
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        size="sm"
                                        onClick={() => void versionsQuery.refetch()}
                                    >
                                        <RefreshCw/>
                                        Retry
                                    </Button>
                                </div>
                            </div>
                        ) : versions.length === 0 ? (
                            <div className={styles.empty}>
                                No document versions uploaded yet.
                            </div>
                        ) : (
                            <div className={styles.versions}>
                                {versions.map((version) => {
                                    const canPublish = (
                                        version.ingestion_status === "ready"
                                        && version.publication_status === "draft"
                                    );

                                    const isPublishing = (
                                        publishMutation.isPending
                                        && publishMutation.variables === version.id
                                    );

                                    return (
                                        <div
                                            key={version.id}
                                            className={styles.versionRow}
                                        >
                                            <div className={styles.versionInfo}>
                                                <span className={styles.versionTitle}>
                                                    <FileText
                                                        className="mr-2 inline size-4"
                                                        aria-hidden="true"
                                                    />
                                                    {version.original_filename}
                                                </span>

                                                <span className={styles.versionMeta}>
                                                    Version {version.version_number}
                                                    {" · "}
                                                    {formatDate(version.created_at)}
                                                    {" · "}
                                                    {formatStatus(version)}
                                                </span>

                                                {version.effective_date && (
                                                    <span className={styles.versionMeta}>
                                                        Effective {version.effective_date}
                                                    </span>
                                                )}

                                                {version.ingestion_status === "processing" && (
                                                    <div
                                                        className={styles.processingStatus}
                                                        role="status"
                                                    >
                                                        <RefreshCw className="size-3.5 animate-spin"/>
                                                        Extracting text and generating embeddings...
                                                    </div>
                                                )}

                                                {version.ingestion_status === "failed" && (
                                                    <p
                                                        className={styles.error}
                                                        role="alert"
                                                    >
                                                        Document processing failed.
                                                        {version.ingestion_error_code && (
                                                            <>
                                                                {" "}Error: {version.ingestion_error_code}
                                                            </>
                                                        )}
                                                    </p>
                                                )}
                                            </div>

                                            <div className={styles.versionActions}>
                                                <Button
                                                    type="button"
                                                    variant="secondary"
                                                    size="sm"
                                                    disabled={busy}
                                                    onClick={() => {
                                                        window.open(
                                                            getPolicyVersionFileUrl(
                                                                policy.id,
                                                                version.id,
                                                            ),
                                                            "_blank",
                                                            "noopener,noreferrer",
                                                        );
                                                    }}
                                                >
                                                    <ExternalLink/>
                                                    View PDF
                                                </Button>

                                                {canPublish && (
                                                    <Button
                                                        type="button"
                                                        variant="primary"
                                                        size="sm"
                                                        disabled={busy}
                                                        onClick={() => handlePublish(version)}
                                                    >
                                                        {isPublishing
                                                            ? "Publishing..."
                                                            : "Publish"}
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </Dialog>
    );
}
