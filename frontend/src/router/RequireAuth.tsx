import { Navigate, Outlet, useLocation } from "react-router";

import { useAuth } from "../providers/AuthProvider";

export function RequireAuth() {
    const { authenticated, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return null;
    }

    if (!authenticated) {
        return <Navigate to="/auth/login" state={{ from: location }} replace />;
    }

    return <Outlet />;
}
