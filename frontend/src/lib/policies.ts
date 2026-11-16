import { apiFetch } from "./api";

export type PolicyCategory =
    | "leave"
    | "remote_work"
    | "working_hours"
    | "communication"
    | "accessibility"
    | "information_security"
    | "other";

export type PolicyIngestionStatus =
    | "pending"
    | "processing"
    | "ready"
    | "failed";

export type PolicyPublicationStatus =
    | "draft"
    | "published"
    | "archived";

export type PolicyDirectoryStatus =
    | "no_document"
    | "pending"
    | "processing"
    | "ready"
    | "failed"
    | "published"
    | "archived";

export interface PolicyDocument {
    id: string;
    title: string;
    description: string | null;
    category: PolicyCategory;
    created_by: string | null;
    created_at: string;
    updated_at: string;
}

export interface AdminPolicyDocument extends PolicyDocument {
    latest_version_number: number | null;
    status: PolicyDirectoryStatus;
}

export interface PolicyVersion {
    id: string;
    document_id: string;
    version_number: number;
    original_filename: string;
    content_type: string;
    file_size_bytes: number;
    effective_date: string | null;
    ingestion_status: PolicyIngestionStatus;
    publication_status: PolicyPublicationStatus;
    ingestion_error_code: string | null;
    uploaded_by: string | null;
    created_at: string;
    updated_at: string;
    published_at: string | null;
    archived_at: string | null;
}

export interface PolicyDocumentListResponse {
    documents: AdminPolicyDocument[];
}

export interface PolicyVersionListResponse {
    versions: PolicyVersion[];
}

export interface CreatePolicyDocumentRequest {
    title: string;
    description: string | null;
    category: PolicyCategory;
}

export interface PublishedPolicy {
    id: string;
    title: string;
    description: string | null;
    category: PolicyCategory;
    version_id: string;
    version_number: number;
    effective_date: string | null;
    published_at: string;
}

export interface PublishedPolicyListResponse {
    documents: PublishedPolicy[];
}

export interface UploadPolicyVersionInput {
    documentId: string;
    file: File;
    effectiveDate: string | null;
}

export function getPolicyDocuments(): Promise<PolicyDocumentListResponse> {
    return apiFetch<PolicyDocumentListResponse>(
        "/api/admin/policies",
    );
}

export function createPolicyDocument(
    payload: CreatePolicyDocumentRequest,
): Promise<PolicyDocument> {
    return apiFetch<PolicyDocument>(
        "/api/admin/policies",
        {
            method: "POST",
            body: payload,
        },
    );
}

export function getPolicyVersions(
    documentId: string,
): Promise<PolicyVersionListResponse> {
    return apiFetch<PolicyVersionListResponse>(
        `/api/admin/policies/${encodeURIComponent(documentId)}/versions`,
    );
}

export function getPolicyVersionFileUrl(
    documentId: string,
    versionId: string,
    download = false,
): string {
    const path = (
        `/api/admin/policies/${encodeURIComponent(documentId)}`
        + `/versions/${encodeURIComponent(versionId)}/file`
    );

    return download ? `${path}?download=true` : path;
}

export function getPublishedPolicies(): Promise<PublishedPolicyListResponse> {
    return apiFetch<PublishedPolicyListResponse>(
        "/api/policies",
    );
}

export function uploadPolicyVersion({
    documentId,
    file,
    effectiveDate,
}: UploadPolicyVersionInput): Promise<PolicyVersion> {
    const formData = new FormData();

    formData.append("file", file);

    if (effectiveDate) {
        formData.append("effective_date", effectiveDate);
    }

    return apiFetch<PolicyVersion>(
        `/api/admin/policies/${encodeURIComponent(documentId)}/versions`,
        {
            method: "POST",
            body: formData,
        },
    );
}

export function publishPolicyVersion(
    documentId: string,
    versionId: string,
): Promise<PolicyVersion> {
    return apiFetch<PolicyVersion>(
        `/api/admin/policies/${encodeURIComponent(documentId)}/versions/${encodeURIComponent(versionId)}/publish`,
        {
            method: "POST",
        },
    );
}

export function getPublishedPolicyFileUrl(
    documentId: string,
    download = false,
): string {
    const path = `/api/policies/${encodeURIComponent(documentId)}/file`;

    return download ? `${path}?download=true` : path;
}

export function getCitedPolicyFileUrl(
    documentId: string,
    versionId: string,
    pageNumber: number | null,
): string {
    const path = (
        `/api/policies/${encodeURIComponent(documentId)}`
        + `/versions/${encodeURIComponent(versionId)}/file`
    );

    return pageNumber !== null && pageNumber > 0
        ? `${path}#page=${pageNumber}`
        : path;
}
