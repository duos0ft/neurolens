import { createRoot } from "react-dom/client";
import { Auth0Provider } from "@auth0/auth0-react";
import { RouterProvider } from "react-router/dom";

import { router } from "./router";
import "./styles/global.css";

const domain = import.meta.env.PUBLIC_AUTH0_DOMAIN;
const clientId = import.meta.env.PUBLIC_AUTH0_CLIENT_ID;

const root = document.getElementById("root");

if (!root) {
    throw new Error("Root element not found");
}

createRoot(root).render(
    <Auth0Provider
        domain={domain}
        clientId={clientId}
        authorizationParams={{
            redirect_uri: window.location.origin,
        }}
        cacheLocation="memory"
    >
        <RouterProvider router={router}/>
    </Auth0Provider>,
);