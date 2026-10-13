import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { Outlet } from "react-router";

import { Sidebar } from "../components/sidebar/Sidebar";
import { appLayoutStyles as styles } from "./AppLayout.styles";
import { useAuth } from "../providers/AuthProvider";

export function AppLayout() {
    const { employee } = useAuth();
    const [ mobileOpen, setMobileOpen ] = useState(false);

    const isAdmin = employee?.role === "admin";

    useEffect(() => {
        if (!mobileOpen) return;

        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setMobileOpen(false);
            }
        }

        window.addEventListener("keydown", handleKeyDown);

        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [ mobileOpen ]);

    return (
        <div className={styles.root}>
            {mobileOpen && (
                <button
                    type="button"
                    className={styles.backdrop}
                    aria-label="Close navigation"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            <Sidebar isAdmin={isAdmin} mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />

            <div className={styles.content}>
                <header className={styles.header}>
                    <button
                        type="button"
                        className={styles.mobileToggle}
                        aria-label="Open navigation"
                        aria-expanded={mobileOpen}
                        onClick={() => setMobileOpen(true)}
                    >
                        <Menu className={styles.toggleIcon} />
                    </button>
                </header>

                <main className={styles.main}>
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
