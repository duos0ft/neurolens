import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router/dom";

import { AuthProvider } from "./providers/AuthProvider";
import { router } from "./router/router";

import "./styles/global.css";
import { Toast } from "./components/toast";

const root = document.getElementById("root");

if (!root) {
    throw new Error("Root element not found");
}

createRoot(root).render(
    <AuthProvider>
        <RouterProvider router={router}/>
        <Toast/>
    </AuthProvider>,
);
