import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router";

import { Button } from "../../components/button";
import { Loading } from "../../components/loading";
import { logout } from "../../lib/auth";
import { useAuth } from "../../providers/AuthProvider";

export function Component() {
    const {
        authenticated,
        loading,
        invalidateSession,
    } = useAuth();

    const logoutStarted = useRef(false);
    const [ error, setError ] = useState(false);

    useEffect(() => {
        if (loading || !authenticated || logoutStarted.current) {
            return;
        }

        logoutStarted.current = true;

        async function startLogout() {
            try {

                const response = await logout();

                invalidateSession();

                window.location.replace(response.logout_url);
            } catch {
                setError(true);
                logoutStarted.current = false;
            }
        }

        void startLogout();
    }, [ loading, authenticated, invalidateSession ]);

    if (loading) {
        return <Loading title="Checking your session..."/>;
    }

    if (!authenticated && !logoutStarted.current && !error) {
        return <Navigate to="/auth/logged-out" replace/>;
    }

    if (error) {
        return (
            <div className="flex flex-col items-center gap-4 text-center">
                <h1 className="text-title font-semibold text-fg">
                    Unable to sign out
                </h1>

                <p className="text-sm text-fg-muted">
                    We couldn't complete sign-out. Please try again.
                </p>

                <Button
                    variant="primary"
                    onClick={() => {
                        setError(false);
                        logoutStarted.current = false;
                        window.location.reload();
                    }}
                >
                    Try again
                </Button>
            </div>
        );
    }

    return (
        <Loading
            size="xl"
            title="Signing you out"
            description="Ending your secure session..."
        />
    );
}
