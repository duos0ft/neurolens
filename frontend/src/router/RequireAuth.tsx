import { Navigate, Outlet, useLocation } from "react-router";

import { Button } from "../components/button";
import { Loading } from "../components/loading";
import { AuthLayout } from "../layouts/AuthLayout";
import { useAuth } from "../providers/AuthProvider";

export function RequireAuth() {
    const { status, revalidateSession } = useAuth();
    const location = useLocation();

    if (status === "loading") {
        return (
            <AuthLayout>
                <Loading
                    size="xl"
                    title="Checking your session"
                    description="Please wait a moment..."
                />
            </AuthLayout>
        );
    }

    if (status === "connection-error") {
        return (
            <AuthLayout>
                <div className="flex flex-col items-center gap-4">
                    <h1 className="text-xl font-semibold text-fg">
                        Connection unavailable
                    </h1>

                    <p className="max-w-sm text-sm text-fg-muted">
                        We couldn't verify your NeuroLens session.
                        Check your connection and try again.
                    </p>

                    <Button
                        variant="primary"
                        onClick={() => void revalidateSession()}
                    >
                        Try again
                    </Button>
                </div>
            </AuthLayout>
        );
    }

    if (status === "unauthenticated") {
        return <Navigate to="/auth/login" state={{ from: location }} replace/>;
    }

    return <Outlet/>;
}
