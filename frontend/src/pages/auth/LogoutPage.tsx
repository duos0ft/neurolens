import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router";

import { Loading } from "../../components/loading";
import { logout } from "../../lib/auth";
import { useAuth } from "../../providers/AuthProvider";

export function Component() {
    const { authenticated, loading } = useAuth();
    const logoutStarted = useRef(false);
    const [ error, setError ] = useState(false);

    useEffect(() => {
        if (loading || !authenticated || logoutStarted.current) {
            return;
        }

        logoutStarted.current = true;

        async function startLogout() {
            try {
                await logout();
            } catch {
                setError(true);
                logoutStarted.current = false;
            }
        }

        void startLogout();
    }, [ loading, authenticated ]);

    if (loading) {
        return <Loading title="Checking your session..."/>;
    }

    if (!authenticated) {
        return <Navigate to="/auth/logged-out" replace/>;
    }

    if (error) {
        return (
            <div className="text-center">
                <h1 className="text-title font-semibold text-fg">Unable to sign out</h1>
                <p className="mt-2 text-sm text-fg-muted">Please try again.</p>
            </div>
        );
    }

    return <Loading size="xl" title="Signing you out" description="Ending your secure session..."/>;
}
