import { ApiError } from "./api";

export interface InvitationDetails {
    email: string;
    role: "admin" | "employee";
    expires_at: string;
}

interface InvitationLoginResponse {
    authorization_url: string;
}

async function invitationRequest<T>(
    path: string,
    token: string,
): Promise<T> {
    const response = await fetch(path, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({ token }),
    });

    if (!response.ok) {
        throw new ApiError(
            response.status,
            "This invitation is invalid or no longer available.",
        );
    }

    return response.json() as Promise<T>;
}

export function validateInvitation(
    token: string,
): Promise<InvitationDetails> {
    return invitationRequest<InvitationDetails>(
        "/api/auth/invitations/validate",
        token,
    );
}

export function loginWithInvitation(
    token: string,
): Promise<InvitationLoginResponse> {
    return invitationRequest<InvitationLoginResponse>(
        "/api/auth/invitations/login",
        token,
    );
}
