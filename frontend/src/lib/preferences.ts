import { apiFetch } from "./api";

export interface EmployeePreferences {
    directness: "low" | "balanced" | "high";
    response_length: "short" | "medium" | "detailed";
    highlight_ambiguity: boolean;
    step_by_step_guidance: boolean;
    always_show_next_step: boolean;
}

export type UpdateEmployeePreferences = Partial<EmployeePreferences>;

export function getPreferences(): Promise<EmployeePreferences> {
    return apiFetch<EmployeePreferences>("/api/preferences");
}

export function updatePreferences(
    preferences: UpdateEmployeePreferences,
): Promise<EmployeePreferences> {
    return apiFetch<EmployeePreferences>("/api/preferences", {
        method: "PATCH",
        body: preferences,
    });
}
