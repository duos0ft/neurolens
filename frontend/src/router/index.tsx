import { createBrowserRouter, Navigate } from "react-router";

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