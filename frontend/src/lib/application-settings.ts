import { apiFetch } from "./api";

export interface ApplicationSettings {
    organization_name: string;
    enable_task_assistance: boolean;
    enable_policy_assistance: boolean;
    enable_sentiment_analysis: boolean;
    created_at: string;
    updated_at: string;
}

export type UpdateApplicationSettings = Partial<
    Pick<
        ApplicationSettings,
        | "organization_name"
        | "enable_task_assistance"
        | "enable_policy_assistance"
        | "enable_sentiment_analysis"
    >
>;

export function getApplicationSettings(): Promise<ApplicationSettings> {
    return apiFetch<ApplicationSettings>("/api/admin/settings");
}

export function updateApplicationSettings(
    settings: UpdateApplicationSettings,
): Promise<ApplicationSettings> {
    return apiFetch<ApplicationSettings>("/api/admin/settings", {
        method: "PATCH",
        body: settings,
    });
}
