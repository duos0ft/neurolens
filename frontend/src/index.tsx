import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router/dom";

import { Toast } from "./components/toast";
import { AuthProvider } from "./providers/AuthProvider";
import { router } from "./router/router";

import "./styles/global.css";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
});

const root = document.getElementById("root");

if (!root) {
    throw new Error("Root element not found");
}

createRoot(root).render(
    <QueryClientProvider client={queryClient}>
        <AuthProvider>
            <RouterProvider router={router}/>
            <Toast/>
        </AuthProvider>
    </QueryClientProvider>,
);
