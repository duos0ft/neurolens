import type { ProfileFormValues } from "../pages/profile/ProfilePage.schema";
import type { AuthenticatedEmployee } from "../types/auth";
import { apiFetch } from "./api";

export function updateProfile(
    values: ProfileFormValues,
): Promise<AuthenticatedEmployee> {
    const payload = Object.fromEntries(
        Object.entries(values).map(([ key, value ]) => [
            key,
            value.trim() || null,
        ]),
    );

    return apiFetch<AuthenticatedEmployee>("/api/profile", {
        method: "PATCH",
        body: payload,
    });
}
