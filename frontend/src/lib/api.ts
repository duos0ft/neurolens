interface CsrfResponse {
    csrf_token: string;
}

type UnauthorizedHandler = () => void;

let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(
    handler: UnauthorizedHandler | null,
): void {
    unauthorizedHandler = handler;
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

function handleApiError(
    response: Response,
    message: string,
): never {
    if (response.status === 401) {
        unauthorizedHandler?.();
    }

    throw new ApiError(response.status, message);
}

async function getCsrfToken(): Promise<string> {
    const response = await fetch("/api/auth/csrf", {
        credentials: "same-origin",
        cache: "no-store",
    });

    if (!response.ok) {
        return handleApiError(
            response,
            "Unable to retrieve CSRF token.",
        );
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

    if (options.body instanceof FormData) {
        headers.delete("Content-Type");
        body = options.body;
    } else if (options.body !== undefined) {
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
        return handleApiError(
            response,
            `Request failed (${response.status}).`,
        );
    }

    if (response.status === 204) {
        return undefined as T;
    }

    return (await response.json()) as T;
}
