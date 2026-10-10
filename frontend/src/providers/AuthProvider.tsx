import { createContext, type PropsWithChildren, useContext, useEffect, useState } from "react";

import type { AuthenticatedEmployee } from "../types/auth";

interface AuthContextValue {
    employee: AuthenticatedEmployee | null;
    authenticated: boolean;
    loading: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
    const [ employee, setEmployee ] = useState<AuthenticatedEmployee | null>(null);
    const [ loading, setLoading ] = useState(true);

    useEffect(() => {
        const controller = new AbortController();

        async function restoreSession() {
            try {
                const response = await fetch("/api/auth/me", {
                    credentials: "same-origin",
                    signal: controller.signal,
                    cache: "no-store",
                });

                if (!response.ok) {
                    throw new Error("Session unavailable");
                }

                const data: AuthenticatedEmployee = await response.json();

                setEmployee(data);
            } catch {
                if (!controller.signal.aborted) {
                    setEmployee(null);
                }
            } finally {
                if (!controller.signal.aborted) {
                    setLoading(false);
                }
            }
        }

        void restoreSession();

        return () => controller.abort();
    }, []);

    return (
        <AuthContext.Provider value={{ employee, authenticated: employee !== null, loading }}>
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
