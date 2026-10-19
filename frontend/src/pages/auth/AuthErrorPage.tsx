import { AlertCircle, ArrowRight } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router";

import { Button } from "../../components/button";
import { Card } from "../../components/card";
import { cn } from "../../lib/cn";
import { authResultStyles as styles } from "./AuthResult.styles";

const errorMessages: Record<string, string> = {
    invalid_state: "Your sign-in session expired or could not be verified.",
    authentication_failed: "We couldn't complete your authentication.",
    missing_code: "The authentication response was incomplete.",
    invalid_token: "We couldn't verify your identity.",
    access_denied: "Your account doesn't have access to NeuroLens.",
};

export function Component() {
    const navigate = useNavigate();
    const [ searchParams ] = useSearchParams();

    const reason = searchParams.get("reason") ?? "";
    const description = errorMessages[reason] ?? "Something went wrong while signing you in. Please try again.";

    return (
        <div className={styles.root}>
            <Card variant="flat" padding="lg" className={styles.card}>
                <div className={cn(styles.icon, styles.errorIcon)} aria-hidden="true">
                    <AlertCircle className={styles.iconSvg} strokeWidth={1.75} />
                </div>

                <div className={styles.content}>
                    <h1 className={styles.title}>Unable to sign in</h1>
                    <p className={styles.description}>{description}</p>
                </div>

                <Button variant="primary" className={styles.action} onClick={() => navigate("/auth/login")}>
                    Try again
                    <ArrowRight />
                </Button>
            </Card>
        </div>
    );
}
