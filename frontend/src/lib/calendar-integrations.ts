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
