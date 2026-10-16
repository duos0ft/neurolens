interface CsrfResponse {
    csrf_token: string;
}

export class ApiError extends Error {
    constructor(
        public readonly status: number,
        message: string,
    ) {
        super(message);
        this.name = "ApiError";
    }
}

async function getCsrfToken(): Promise<string> {
    const response = await fetch("/api/auth/csrf", {
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new ApiError(response.status, "Unable to retrieve CSRF token.");
    }

    const data: CsrfResponse = await response.json();
    return data.csrf_token;
}

type ApiOptions = Omit<RequestInit, "body"> & {
    body?: unknown;
};

export async function apiFetch<T>(
    path: string,
    options: ApiOptions = {},
): Promise<T> {
    const method = (options.method ?? "GET").toUpperCase();

    const headers = new Headers(options.headers);

    if (![ "GET", "HEAD", "OPTIONS" ].includes(method)) {
        const csrfToken = await getCsrfToken();
        headers.set("X-CSRF-Token", csrfToken);
    }

    let body: BodyInit | undefined;

    if (options.body !== undefined) {
        headers.set("Content-Type", "application/json");
        body = JSON.stringify(options.body);
    }

    const response = await fetch(path, {
        ...options,
        method,
        headers,
        body,
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new ApiError(response.status, `Request failed (${response.status}).`);
    }

    if (response.status === 204) {
        return undefined as T;
    }

    return (await response.json()) as T;
}
