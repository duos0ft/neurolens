import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Pencil, Plus, RefreshCw } from "lucide-react";

import { Button } from "../../components/button";
import { PageHeader } from "../../components/page-header/PageHeader";
import { Table, type TableColumn, type TableRowAction } from "../../components/table/Table";
import {
    getPolicyDocuments,
    getPublishedPolicies,
    getPublishedPolicyFileUrl,
    type PolicyCategory,
    type PolicyDocument,
} from "../../lib/policies";
import { useAuth } from "../../providers/AuthProvider";
import { CreatePolicyDialog } from "./CreatePolicyDialog";
import { PolicyDetailsDialog } from "./PolicyDetailsDialog";
import { policiesPageStyles as styles } from "./PoliciesPage.styles";

interface PolicyRow {
    id: string;
    title: string;
    description: string | null;
    category: PolicyCategory;
    updatedAt: string | null;
    versionNumber: number | null;
}

const categoryLabels: Record<PolicyCategory, string> = {
    leave: "Leave",
    remote_work: "Remote work",
    working_hours: "Working hours",
    communication: "Communication",
    accessibility: "Accessibility",
    information_security: "Information security",
    other: "Other",
};

const columns: TableColumn<PolicyRow>[] = [
    {
        key: "title",
        title: "Policy",
        render: (policy) => (
            <div className={styles.policyCell}>
                <span className={styles.policyTitle}>
                    {policy.title}
                </span>

                {policy.description && (
                    <span className={styles.policyDescription}>
                        {policy.description}
                    </span>
                )}
            </div>
        ),
    },
    {
        key: "category",
        title: "Category",
        render: (policy) => (
            <span className={styles.category}>
                {categoryLabels[policy.category]}
            </span>
        ),
    },
    {
        key: "version",
        title: "Version",
        render: (policy) => (
            <span className={styles.date}>
                {policy.versionNumber !== null
                    ? `Version ${policy.versionNumber}`
                    : "—"}
            </span>
        ),
    },
    {
        key: "updatedAt",
        title: "Last updated",
        render: (policy) => (
            <span className={styles.date}>
                {policy.updatedAt
                    ? new Date(policy.updatedAt).toLocaleDateString(
                        undefined,
                        {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                        },
                    )
                    : "—"}
            </span>
        ),
    },
];

export function Component() {
    const { employee } = useAuth();
    const isAdmin = employee?.role === "admin";

    const queryClient = useQueryClient();

    const [ createOpen, setCreateOpen ] = useState(false);
    const [ selectedPolicy, setSelectedPolicy ] = useState<PolicyDocument | null>(null);

    const adminPoliciesQuery = useQuery({
        queryKey: [ "admin", "policies" ],
        queryFn: getPolicyDocuments,
        enabled: isAdmin,
    });

    const publishedPoliciesQuery = useQuery({
        queryKey: [ "policies", "published" ],
        queryFn: getPublishedPolicies,
        enabled: !isAdmin && employee != null,
    });

    const policies: PolicyRow[] = isAdmin
        ? (adminPoliciesQuery.data?.documents ?? []).map((policy) => ({
            id: policy.id,
            title: policy.title,
            description: policy.description,
            category: policy.category,
            updatedAt: policy.updated_at,
            versionNumber: null,
        }))
        : (publishedPoliciesQuery.data?.documents ?? []).map((policy) => ({
            id: policy.id,
            title: policy.title,
            description: policy.description,
            category: policy.category,
            updatedAt: policy.published_at,
            versionNumber: policy.version_number,
        }));

    const loading = isAdmin
        ? adminPoliciesQuery.isPending
        : publishedPoliciesQuery.isPending;

    const hasError = isAdmin
        ? adminPoliciesQuery.isError
        : publishedPoliciesQuery.isError;

    function handlePolicyCreated() {
        void queryClient.invalidateQueries({
            queryKey: [ "admin", "policies" ],
        });
    }

    function openPolicyDetails(row: PolicyRow) {
        const document = adminPoliciesQuery.data?.documents.find(
            (item) => item.id === row.id,
        );

        if (document) {
            setSelectedPolicy(document);
        }
    }

    function openPublishedPolicy(row: PolicyRow) {
        window.open(
            getPublishedPolicyFileUrl(row.id),
            "_blank",
            "noopener,noreferrer",
        );
    }

    function handleRowClick(row: PolicyRow) {
        if (isAdmin) {
            openPolicyDetails(row);
            return;
        }

        openPublishedPolicy(row);
    }

    function retry() {
        if (isAdmin) {
            void adminPoliciesQuery.refetch();
        } else {
            void publishedPoliciesQuery.refetch();
        }
    }

    const rowActions: TableRowAction<PolicyRow>[] = isAdmin
        ? [
            {
                label: "Manage policy",
                icon: Pencil,
                onSelect: openPolicyDetails,
            },
        ]
        : [];

    return (
        <div className={styles.root}>
            <PageHeader
                title="Company policies"
                description="Find and explore your organization's policies and procedures."
                actions={
                    isAdmin ? (
                        <Button
                            type="button"
                            variant="primary"
                            onClick={() => setCreateOpen(true)}
                        >
                            <Plus aria-hidden="true"/>
                            New policy
                        </Button>
                    ) : null
                }
            />

            <section
                className={styles.directory}
                aria-label="Company policy directory"
            >
                {hasError ? (
                    <div className={styles.error} role="alert">
                        <p>Unable to load company policies.</p>

                        <Button
                            type="button"
                            variant="secondary"
                            onClick={retry}
                        >
                            <RefreshCw/>
                            Try again
                        </Button>
                    </div>
                ) : !loading && policies.length === 0 ? (
                    <div className={styles.empty}>
                        <FileText
                            className={styles.emptyIcon}
                            aria-hidden="true"
                        />

                        <h2 className={styles.emptyTitle}>
                            No company policies available
                        </h2>

                        <p className={styles.emptyDescription}>
                            {isAdmin
                                ? "Create a policy and upload a document to start building the company knowledge base."
                                : "Your organization hasn't published any policies yet."}
                        </p>
                    </div>
                ) : (
                    <Table
                        columns={columns}
                        rows={policies}
                        rowKey={(policy) => policy.id}
                        rowActions={rowActions}
                        onRowClick={handleRowClick}
                        loading={loading}
                        emptyMessage="No company policies found."
                    />
                )}
            </section>

            {isAdmin && (
                <>
                    <CreatePolicyDialog
                        open={createOpen}
                        onClose={() => setCreateOpen(false)}
                        onCreated={handlePolicyCreated}
                    />

                    <PolicyDetailsDialog
                        policy={selectedPolicy}
                        onClose={() => setSelectedPolicy(null)}
                    />
                </>
            )}
        </div>
    );
}
