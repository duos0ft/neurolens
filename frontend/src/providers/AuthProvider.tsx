import { createContext, type PropsWithChildren, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { AuthenticatedEmployee } from "../types/auth";
import { setUnauthorizedHandler } from "../lib/api";
import { useQueryClient } from "@tanstack/react-query";

type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "connection-error";

interface AuthContextValue {
    employee: AuthenticatedEmployee | null;
    authenticated: boolean;
    loading: boolean;
    status: AuthStatus;
    updateEmployee: (employee: AuthenticatedEmployee) => void;
    revalidateSession: () => Promise<void>;
    invalidateSession: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
    const [ employee, setEmployee ] = useState<AuthenticatedEmployee | null>(null);
    const [ status, setStatus ] = useState<AuthStatus>("loading");

    const queryClient = useQueryClient();

    const requestVersion = useRef(0);
    const sessionInvalidated = useRef(false);
    const sessionChannel = useRef<BroadcastChannel | null>(null);

    const invalidateSession = useCallback(() => {
        if (sessionInvalidated.current) {
            return;
        }

        sessionInvalidated.current = true;
        requestVersion.current += 1;

        setEmployee(null);
        setStatus("unauthenticated");
        queryClient.clear();

        sessionChannel.current?.postMessage({
            type: "SESSION_INVALIDATED",
        });
    }, [ queryClient ]);

    const revalidateSession = useCallback(async (signal?: AbortSignal) => {
        const version = ++requestVersion.current;

        try {
            const response = await fetch("/api/auth/me", {
                credentials: "same-origin",
                cache: "no-store",
                signal,
            });

            if (signal?.aborted || version !== requestVersion.current) {
                return;
            }

            if (response.status === 401) {
                invalidateSession();
                return;
            }

            if (!response.ok) {
                setStatus("connection-error");
                return;
            }

            const data: AuthenticatedEmployee = await response.json();

            if (
                signal?.aborted
                || version !== requestVersion.current
                || sessionInvalidated.current
            ) {
                return;
            }

            setEmployee(data);
            setStatus("authenticated");
        } catch {
            if (
                !signal?.aborted
                && version === requestVersion.current
                && !sessionInvalidated.current
            ) {
                setStatus("connection-error");
            }
        }
    }, [ invalidateSession ]);

    function updateEmployee(updatedEmployee: AuthenticatedEmployee) {
        setEmployee(updatedEmployee);
        setStatus("authenticated");
    }

    useEffect(() => {
        const controller = new AbortController();

        void revalidateSession(controller.signal);

        return () => controller.abort();
    }, [ revalidateSession ]);

    useEffect(() => {
        function handleVisibilityChange() {
            if (document.visibilityState === "visible") {
                void revalidateSession();
            }
        }

        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            document.removeEventListener("visibilitychange", handleVisibilityChange);
        };
    }, [ revalidateSession ]);

    useEffect(() => {
        setUnauthorizedHandler(invalidateSession);

        return () => {
            setUnauthorizedHandler(null);
        };
    }, [ invalidateSession ]);

    useEffect(() => {
        const channel = new BroadcastChannel("neurolens-session");

        sessionChannel.current = channel;

        channel.onmessage = (event: MessageEvent) => {
            if (event.data?.type === "SESSION_INVALIDATED") {
                invalidateSession();
            }
        };

        return () => {
            sessionChannel.current = null;
            channel.close();
        };
    }, [ invalidateSession ]);

    return (
        <AuthContext.Provider
            value={{
                employee,
                authenticated: status === "authenticated",
                loading: status === "loading",
                status,
                updateEmployee,
                revalidateSession: async () => revalidateSession(),
                invalidateSession,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error("useAuth must be used within AuthProvider");
    }

    return context;
}
