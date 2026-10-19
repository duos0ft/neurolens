import { Navigate, Outlet } from "react-router";

import { useAuth } from "../providers/AuthProvider";

export function RequireAdmin() {
    const { employee, loading } = useAuth();

    if (loading) {
        return null;
    }

    if (employee?.role !== "admin") {
        return <Navigate to="/app" replace/>;
    }

    return <Outlet/>;
}
