import { apiFetch } from "./api";

export interface ContactPerson {
    id: string;
    name: string;
    email: string;
    job_title: string | null;
    department: string | null;
    responsibility: string;
    is_primary: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ContactPersonInput {
    name: string;
    email: string;
    job_title: string | null;
    department: string | null;
    responsibility: string;
    is_primary: boolean;
}

export interface ContactPersonsPage {
    items: ContactPerson[];
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
}

export interface UpdateContactPersonInput extends ContactPersonInput {
    is_active: boolean;
}

export function getContactPersons({
    page = 1,
    pageSize = 20,
    search = "",
    includeInactive = false,
}: {
    page?: number;
    pageSize?: number;
    search?: string;
    includeInactive?: boolean;
} = {}): Promise<ContactPersonsPage> {
    const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        include_inactive: String(includeInactive),
    });

    if (search.trim()) {
        params.set("search", search.trim());
    }

    return apiFetch<ContactPersonsPage>(
        `/api/admin/contact-persons?${params.toString()}`,
    );
}

export function createContactPerson(
    payload: ContactPersonInput,
): Promise<ContactPerson> {
    return apiFetch<ContactPerson>("/api/admin/contact-persons", {
        method: "POST",
        body: payload,
    });
}

export function updateContactPerson(
    contactId: string,
    payload: UpdateContactPersonInput,
): Promise<ContactPerson> {
    return apiFetch<ContactPerson>(
        `/api/admin/contact-persons/${contactId}`,
        {
            method: "PATCH",
            body: payload,
        },
    );
}

export async function deactivateContactPerson(
    contactId: string,
): Promise<ContactPerson> {
    return apiFetch<ContactPerson>(
        `/api/admin/contact-persons/${contactId}/deactivate`,
        {
            method: "POST",
        },
    );
}
