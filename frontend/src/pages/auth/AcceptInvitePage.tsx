import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { Button } from "../../components/button";
import { Loading } from "../../components/loading";
import { loginWithInvitation, validateInvitation } from "../../lib/invitations";

import { acceptInvitePageStyles as styles } from "./AcceptInvitePage.styles";

function readInvitationToken(): string | null {
    const url = new URL(window.location.href);
    const token = url.searchParams.get("token");

    if (token) {
        window.history.replaceState(
            window.history.state,
            "",
            url.pathname + url.hash,
        );
    }

    return token;
}

export function Component() {
    const [ token ] = useState(readInvitationToken);
    const validationStarted = useRef(false);

    const validationMutation = useMutation({
        mutationFn: validateInvitation,
        retry: false,
    });

    const loginMutation = useMutation({
        mutationFn: loginWithInvitation,
        onSuccess: (data) => {
            window.location.replace(data.authorization_url);
        },
    });

    const { mutate: validate } = validationMutation;

    useEffect(() => {
        if (!token || validationStarted.current) {
            return;
        }

        validationStarted.current = true;
        validate(token);
    }, [ token, validate ]);

    if (!token) {
        return (
            <div className={styles.root}>
                <div className={styles.header}>
                    <h1 className={styles.title}>
                        Invitation link required
                    </h1>

                    <p className={styles.description}>
                        Please reopen the invitation link from your email
                        to continue setting up your NeuroLens account.
                    </p>
                </div>

                <Link to="/auth/login" className={styles.link}>
                    Return to login
                </Link>
            </div>
        );
    }

    if (validationMutation.isIdle || validationMutation.isPending) {
        return (
            <Loading
                size="xl"
                title="Checking your invitation"
                description="Please wait while we verify your invitation..."
            />
        );
    }

    if (validationMutation.isError) {
        return (
            <div className={styles.root}>
                <div className={styles.header}>
                    <h1 className={styles.title}>
                        Invitation unavailable
                    </h1>

                    <p className={styles.description}>
                        This invitation may have expired, been cancelled,
                        or already been accepted.
                    </p>
                </div>

                <Link to="/auth/login" className={styles.link}>
                    Return to login
                </Link>
            </div>
        );
    }

    return (
        <div className={styles.root}>
            <div className={styles.header}>
                <h1 className={styles.title}>
                    Welcome to NeuroLens
                </h1>

                <p className={styles.description}>
                    You have been invited to join NeuroLens.
                </p>
            </div>

            <div className={styles.invitationCard}>
                <p className={styles.invitationLabel}>
                    Your invited email
                </p>

                <p className={styles.invitationEmail}>
                    {validationMutation.data.email}
                </p>
            </div>

            <div className={styles.actions}>
                <Button
                    variant="primary"
                    className={styles.button}
                    disabled={loginMutation.isPending}
                    onClick={() => loginMutation.mutate(token)}
                >
                    {loginMutation.isPending
                        ? "Connecting..."
                        : "Continue with Email"}
                </Button>

                {loginMutation.isError && (
                    <p role="alert" className={styles.errorText}>
                        Unable to start authentication. Please try again.
                    </p>
                )}

                <p className={styles.helperText}>
                    You'll verify your email securely through Auth0.
                </p>
            </div>
        </div>
    );
}
