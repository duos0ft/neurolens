export type EmployeeRole = "admin" | "employee";

export type EmployeeStatus = "invited" | "active" | "suspended";

export type InvitationStatus =
    | "pending"
    | "provisioning"
    | "reconciliation_required"
    | "ready"
    | "accepted"
    | "failed"
    | "expired"
    | "cancelled";

export interface Employee {
    id: string;
    email: string | null;
    displayName: string | null;
    role: EmployeeRole;
    status: EmployeeStatus;
    invitationStatus: InvitationStatus | null;
    createdAt: string;
}

export interface PageResponse<T> {
    items: T[];
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
}

export interface PageParams {
    page?: number;
    pageSize?: number;
}

export interface EmployeeFilters extends PageParams {
    search?: string;
    roles?: EmployeeRole[];
    status?: EmployeeStatus;
}
