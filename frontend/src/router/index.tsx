import { createBrowserRouter, Navigate } from "react-router";

import { AuthLayout } from "../layouts/AuthLayout";
import { AppLayout } from "../layouts/AppLayout";
import { RequireAuth } from "./RequireAuth";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <Navigate to="/app" replace />,
    },
    {
        path: "/auth",
        Component: AuthLayout,
        children: [
            {
                index: true,
                element: <Navigate to="/auth/login" replace />,
            },
            {
                path: "login",
                lazy: () => import("../pages/auth/LoginPage"),
            },
            {
                path: "logout",
                lazy: () => import("../pages/auth/LogoutPage"),
            },
            {
                path: "logged-out",
                lazy: () => import("../pages/auth/LoggedOutPage"),
            },
            {
                path: "error",
                lazy: () => import("../pages/auth/AuthErrorPage"),
            },
        ],
    },
    {
        path: "/app",
        Component: RequireAuth,
        children: [
            {
                Component: AppLayout,
                children: [
                    {
                        index: true,
                        lazy: () => import("../pages/dashboard/DashboardPage"),
                    },
                ],
            },
        ],
    },
    {
        path: "*",
        element: <Navigate to="/app" replace />,
    },
]);
