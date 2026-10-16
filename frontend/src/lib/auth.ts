import { apiFetch } from "./api";

interface LogoutResponse {
    logout_url: string;
}

export async function logout(): Promise<void> {
    const response = await apiFetch<LogoutResponse>("/api/auth/logout", {
        method: "POST",
    });

    window.location.replace(response.logout_url);
}
