import { useSearchParams } from "react-router";

import { authErrorPageStyles as styles } from "./AuthErrorPage.styles";

const errorMessages: Record<string, string> = {
    invalid_state: "Your sign-in session expired or could not be verified.",
    authentication_failed: "We couldn't complete your authentication.",
    missing_code: "The authentication response was incomplete.",
    invalid_token: "We couldn't verify your identity.",
    access_denied: "Your account doesn't have access to NeuroLens.",
};

export function Component() {
    const [searchParams] = useSearchParams();
    const reason = searchParams.get("reason") ?? "";

    const description = errorMessages[reason] ?? "Something went wrong while signing you in. Please try again.";

    return (
        <div className={styles.root}>
            <div className={styles.icon} aria-hidden="true">
                <span className="text-hero">!</span>
            </div>

            <div className={styles.content}>
                <h1 className={styles.title}>Unable to sign in</h1>
                <p className={styles.description}>{description}</p>
            </div>

            <a href="/auth/login" className={styles.button}>
                Try again
            </a>
        </div>
    );
}
