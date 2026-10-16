import { apiFetch } from "./api";
import type { Employee, EmployeeFilters, EmployeeRole, EmployeeStatus, PageResponse } from "../types/employee";

interface EmployeeApiResponse {
    id: string;
    email: string | null;
    display_name: string | null;
    role: EmployeeRole;
    status: EmployeeStatus;
    created_at: string;
}

interface PageApiResponse<T> {
    items: T[];
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
}

export async function getEmployees(
    filters: EmployeeFilters = {},
): Promise<PageResponse<Employee>> {
    const params = new URLSearchParams();

    if (filters.page !== undefined) {
        params.set("page", String(filters.page));
    }

    if (filters.pageSize !== undefined) {
        params.set("page_size", String(filters.pageSize));
    }

    if (filters.search?.trim()) {
        params.set("search", filters.search.trim());
    }

    if (filters.role) {
        params.set("role", filters.role);
    }

    if (filters.status) {
        params.set("status", filters.status);
    }

    const query = params.toString();

    const response = await apiFetch<PageApiResponse<EmployeeApiResponse>>(
        `/api/employees/${query ? `?${query}` : ""}`,
    );

    return {
        items: response.items.map((employee) => ({
            id: employee.id,
            email: employee.email,
            displayName: employee.display_name,
            role: employee.role,
            status: employee.status,
            createdAt: employee.created_at,
        })),
        page: response.page,
        pageSize: response.page_size,
        totalItems: response.total_items,
        totalPages: response.total_pages,
    };
}
