import { apiFetch } from "./api";

export type CalendarIntegrationProvider = "google" | "microsoft";

export interface CalendarIntegrationStatus {
    provider: CalendarIntegrationProvider;
    connected: boolean;
    integration_id: string | null;
    account_email: string | null;
    connected_at: string | null;
}

export interface CalendarAuthorizationResponse {
    authorization_url: string;
}

export interface CalendarDisconnectResponse {
    provider: CalendarIntegrationProvider;
    disconnected: boolean;
}

export interface CalendarSyncRequestResponse {
    queued: boolean;
    task_count: number;
    event_count: number;
    deletion_count: number;
}

export interface CalendarIntegrationStatus {
    provider: CalendarIntegrationProvider;
    connected: boolean;
    integration_id: string | null;
    account_email: string | null;
    connected_at: string | null;
    last_synced_at: string | null;
    pending_count: number;
    syncing_count: number;
    failed_count: number;
}

export function getGoogleCalendarStatus(): Promise<CalendarIntegrationStatus> {
    return apiFetch<CalendarIntegrationStatus>(
        "/api/integrations/google-calendar/status",
    );
}

export function connectGoogleCalendar(): Promise<CalendarAuthorizationResponse> {
    return apiFetch<CalendarAuthorizationResponse>(
        "/api/integrations/google-calendar/connect",
        {
            method: "POST",
        },
    );
}

export function disconnectGoogleCalendar(): Promise<CalendarDisconnectResponse> {
    return apiFetch<CalendarDisconnectResponse>(
        "/api/integrations/google-calendar",
        {
            method: "DELETE",
        },
    );
}

export function syncGoogleCalendar(): Promise<CalendarSyncRequestResponse> {
    return apiFetch<CalendarSyncRequestResponse>(
        "/api/integrations/google-calendar/sync",
        {
            method: "POST",
        },
    );
}
