import { useEffect, useRef } from "react";
import { Navigate } from "react-router";

import { Loading } from "../../components/loading";
import { useAuth } from "../../providers/AuthProvider";

export function Component() {
    const { authenticated, loading } = useAuth();
    const redirectStarted = useRef(false);

    useEffect(() => {
        if (loading || authenticated || redirectStarted.current) {
            return;
        }

        redirectStarted.current = true;
        window.location.replace("/api/auth/login");
    }, [loading, authenticated]);

    if (loading) {
        return <Loading size="xl" title="Checking your session" description="Please wait a moment..." />;
    }

    if (authenticated) {
        return <Navigate to="/app" replace />;
    }

    return <Loading size="xl" title="Signing you in" description="Connecting securely to NeuroLens..." />;
}
