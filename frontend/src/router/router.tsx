import { createBrowserRouter, Navigate } from "react-router";

import { AuthLayout } from "../layouts/AuthLayout";
import { AppLayout } from "../layouts/AppLayout";
import { RequireAdmin } from "./RequireAdmin";
import { RequireAuth } from "./RequireAuth";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <Navigate to="/app/chat" replace/>,
    },
    {
        path: "/auth",
        Component: AuthLayout,
        children: [
            {
                index: true,
                element: <Navigate to="/auth/login" replace/>,
            },
            {
                path: "login",
                lazy: () => import("../pages/auth/LoginPage"),
            },
            {
                path: "accept-invite",
                lazy: () => import("../pages/auth/AcceptInvitePage"),
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
                        element: <Navigate to="/app/chat" replace/>,
                    },
                    {
                        path: "my-tasks",
                        lazy: () => import("../pages/tasks/TasksPage"),
                    },
                    {
                        path: "calendar",
                        lazy: () => import("../pages/calendar/CalendarPage"),
                    },
                    {
                        path: "profile",
                        lazy: () => import("../pages/profile/ProfilePage"),
                    },
                    {
                        path: "preferences",
                        lazy: () => import("../pages/preferences/PreferencesPage"),
                    },
                    {
                        path: "chat",
                        lazy: () => import("../pages/chat/ChatPage"),
                    },
                    {
                        path: "policies",
                        lazy: () => import("../pages/policies/PoliciesPage"),
                    },
                    {
                        Component: RequireAdmin,
                        children: [
                            {
                                path: "admin/employees",
                                lazy: () => import("../pages/admin/employees/EmployeesPage"),
                            },
                            {
                                path: "admin/contact-persons",
                                lazy: () => import("../pages/admin/contact-persons/ContactPersonsPage"),
                            },
                            {
                                path: "admin/settings",
                                lazy: () => import("../pages/admin/settings/AdminSettingsPage"),
                            },
                        ],
                    },
                ],
            },
        ],
    },
    {
        path: "*",
        element: <Navigate to="/app/chat" replace/>,
    },
]);
