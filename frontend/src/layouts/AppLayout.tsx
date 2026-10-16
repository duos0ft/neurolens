import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { Link, Outlet, useMatches } from "react-router";

import { Sidebar } from "../components/sidebar/Sidebar";
import { useAuth } from "../providers/AuthProvider";
import { appLayoutStyles as styles } from "./AppLayout.styles";

const breadcrumbLabels: Record<string, string> = {
    "/app": "Dashboard",
    "/app/profile": "My profile",
    "/app/admin/employees": "Employees",
    "/app/admin/invitations": "Invitations",
};

export function AppLayout() {
    const { employee } = useAuth();
    const matches = useMatches();
    const [ mobileOpen, setMobileOpen ] = useState(false);

    const isAdmin = employee?.role === "admin";

    const currentPath = matches[matches.length - 1]?.pathname ?? "/app";
    const currentPage = breadcrumbLabels[currentPath] ?? "NeuroLens";
    const isAdminPage = currentPath.startsWith("/app/admin/");

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

            <Sidebar
                isAdmin={isAdmin}
                mobileOpen={mobileOpen}
                onNavigate={() => setMobileOpen(false)}
            />

            <div className={styles.content}>
                <header className={styles.header}>
                    <button
                        type="button"
                        className={styles.mobileToggle}
                        aria-label="Open navigation"
                        aria-expanded={mobileOpen}
                        onClick={() => setMobileOpen(true)}
                    >
                        <Menu className={styles.toggleIcon}/>
                    </button>

                    <nav aria-label="Breadcrumb" className={styles.breadcrumbs}>
                        {isAdminPage ? (
                            <>
                                <span className={styles.breadcrumbParent}>
                                    Organisation
                                </span>
                                <span className={styles.breadcrumbSeparator}>/</span>
                            </>
                        ) : currentPath !== "/app" ? (
                            <>
                                <Link to="/app" className={styles.breadcrumbLink}>
                                    Home
                                </Link>
                                <span className={styles.breadcrumbSeparator}>/</span>
                            </>
                        ) : null}

                        <span className={styles.breadcrumbCurrent} aria-current="page">
                            {currentPage}
                        </span>
                    </nav>
                </header>

                <main className={styles.main}>
                    <div className={styles.mainInner}>
                        <Outlet/>
                    </div>
                </main>
            </div>
        </div>
    );
}
