import { createBrowserRouter, Navigate } from "react-router";
import { RequireAuth } from "./RequireAuth";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <Navigate to="/app" replace/>,
    },
    {
        path: "/login",
        lazy: () => import("../pages/auth/LoginPage"),
    },
    {
        path: "/app",
        Component: RequireAuth,
        children: [
            {
                index: true,
                lazy: () => import("../pages/dashboard/DashboardPage"),
            },
        ],
    },
    {
        path: "*",
        element: <Navigate to="/app" replace/>,
    },
]);