import { createContext, type PropsWithChildren, useContext, useEffect, useState, } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";

interface AuthContextValue {
    user: User | null;
    session: Session | null;
    loading: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(
    undefined,
);

export function AuthProvider({ children }: PropsWithChildren) {
    const [ session, setSession ] = useState<Session | null>(null);
    const [ loading, setLoading ] = useState(true);

    useEffect(() => {
        let active = true;

        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (_event, nextSession) => {
                if (!active) return;

                setSession(nextSession);
                setLoading(false);
            },
        );

        return () => {
            active = false;
            subscription.unsubscribe();
        };
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user: session?.user ?? null,
                session,
                loading,
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