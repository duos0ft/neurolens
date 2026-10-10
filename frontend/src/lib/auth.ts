interface LogoutOptions {
    csrfToken: string;
}

export function logout({ csrfToken }: LogoutOptions): void {
    const form = document.createElement("form");

    form.method = "POST";
    form.action = "/api/auth/logout";
    form.style.display = "none";

    const csrfInput = document.createElement("input");
    csrfInput.type = "hidden";
    csrfInput.name = "csrf_token";
    csrfInput.value = csrfToken;

    form.appendChild(csrfInput);
    document.body.appendChild(form);

    form.submit();
}
