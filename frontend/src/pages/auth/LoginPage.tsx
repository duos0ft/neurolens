import { useAuth0 } from "@auth0/auth0-react";
import { Navigate } from "react-router";

export function Component() {
    const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0();

    if (isLoading) {
        return null;
    }

    if (isAuthenticated) {
        return <Navigate to="/app" replace/>;
    }

    return (
        <main className="flex min-h-screen items-center justify-center bg-bg px-6">
            <div className="w-full max-w-md text-center">
                <div className="mx-auto mb-8 size-20 rounded-full bg-orb shadow-orb"/>

                <h1 className="text-hero font-semibold text-fg">
                    Welcome to NeuroLens
                </h1>

                <p className="mt-3 text-fg-body">
                    A calmer, clearer way to navigate your workday.
                </p>

                <button
                    type="button"
                    onClick={() => void loginWithRedirect()}
                    className="mt-8 h-control-xl w-full rounded-md bg-primary px-6 font-medium text-on-primary transition-colors duration-fast hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                >
                    Continue with NeuroLens
                </button>

                <p className="mt-6 text-sm text-fg-muted">
                    Access is available to authorized employees only.
                </p>
            </div>
        </main>
    );
}