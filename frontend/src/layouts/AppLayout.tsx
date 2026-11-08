import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { Outlet, useLocation } from "react-router";

import { Sidebar } from "../components/sidebar/Sidebar";
import { useAuth } from "../providers/AuthProvider";
import { appLayoutStyles as styles } from "./AppLayout.styles";

export function AppLayout() {
    const { employee } = useAuth();
    const location = useLocation();

    const [ mobileOpen, setMobileOpen ] = useState(false);

    const isAdmin = employee?.role === "admin";
    const isWorkspace = location.pathname === "/app/chat";

    useEffect(() => {
        setMobileOpen(false);
    }, [ location.pathname ]);

    useEffect(() => {
        if (!mobileOpen) {
            return;
        }

        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setMobileOpen(false);
            }
        }

        window.addEventListener("keydown", handleKeyDown);

        return () => {
            window.removeEventListener("keydown", handleKeyDown);
        };
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

            <Sidebar
                isAdmin={isAdmin}
                mobileOpen={mobileOpen}
                onNavigate={() => setMobileOpen(false)}
            />

            <div className={styles.content}>
                <div className={styles.mobileHeader}>
                    <button
                        type="button"
                        className={styles.mobileToggle}
                        aria-label="Open navigation"
                        aria-expanded={mobileOpen}
                        onClick={() => setMobileOpen(true)}
                    >
                        <Menu className={styles.toggleIcon}/>
                    </button>
                </div>

                <main
                    className={
                        isWorkspace
                            ? styles.workspaceMain
                            : styles.main
                    }
                >
                    <div
                        className={
                            isWorkspace
                                ? styles.workspaceMainInner
                                : styles.mainInner
                        }
                    >
                        <Outlet/>
                    </div>
                </main>
            </div>
        </div>
    );
}
