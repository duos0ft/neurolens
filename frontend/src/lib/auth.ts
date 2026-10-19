import { apiFetch } from "./api";

interface LogoutResponse {
    logout_url: string;
}

export function logout(): Promise<LogoutResponse> {
    return apiFetch<LogoutResponse>("/api/auth/logout", {
        method: "POST",
    });
}
