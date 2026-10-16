import { useState } from "react";
import {
    BookOpen,
    CalendarDays,
    ChevronDown,
    ListTodo,
    Mail,
    MessageSquare,
    Settings,
    Shield,
    Users,
} from "lucide-react";
import { useLocation } from "react-router";

import { cn } from "../../lib/cn";
import { SidebarItem } from "./SidebarItem";
import { sidebarStyles as styles } from "./Sidebar.styles";
import { Button } from "../button";
import { SidebarAccount } from "./SidebarAccount";

const navigation = [
    { label: "Assistant", path: "/assistant", icon: MessageSquare },
    { label: "Tasks", path: "/tasks", icon: ListTodo },
    { label: "Calendar", path: "/calendar", icon: CalendarDays },
    { label: "Policies", path: "/policies", icon: BookOpen },
];

const adminNavigation = [
    { label: "Employees", path: "/app/admin/employees", icon: Users },
    { label: "Invitations", path: "/app/admin/invitations", icon: Mail },
    { label: "Settings", path: "/app/admin/settings", icon: Settings },
];

type SidebarProps = {
    isAdmin: boolean;
    mobileOpen: boolean;
    onNavigate: () => void;
};

export function Sidebar({ isAdmin, mobileOpen, onNavigate }: SidebarProps) {
    const location = useLocation();
    const isAdminRoute = location.pathname === "/admin" || location.pathname.startsWith("/admin/");

    const [ adminOverride, setAdminOverride ] = useState<{
        pathname: string;
        expanded: boolean;
    } | null>(null);

    const showAdminNavigation = adminOverride?.pathname === location.pathname ? adminOverride.expanded : isAdminRoute;

    return (
        <aside
            className={cn(
                styles.root,
                "fixed inset-y-0 left-0 z-50 w-64 transition-transform duration-200 ease-in-out",
                "lg:sticky lg:top-0 lg:z-auto lg:h-dvh lg:translate-x-0",
                mobileOpen ? "translate-x-0" : "-translate-x-full",
            )}
            aria-label="Application navigation"
        >
            <div className={styles.header}>
                <div className={cn(styles.logo, "bg-gradient-to-br from-sky-300 via-blue-500 to-blue-700")}/>
                <span className={styles.brand}>NeuroLens</span>
            </div>

            <div className={styles.content}>
                <nav className={styles.nav} aria-label="Main navigation">
                    {navigation.map(({ label, path, icon }) => (
                        <SidebarItem key={path} label={label} to={path} icon={icon} onNavigate={onNavigate}/>
                    ))}
                </nav>

                {isAdmin && (
                    <div className={styles.section}>
                        <Button
                            variant="ghost"
                            className={cn(styles.adminToggle, isAdminRoute && styles.navLinkActive)}
                            onClick={() =>
                                setAdminOverride({
                                    pathname: location.pathname,
                                    expanded: !showAdminNavigation,
                                })
                            }
                            aria-expanded={showAdminNavigation}
                            aria-controls="sidebar-admin-navigation"
                        >
                            <span className={styles.adminToggleContent}>
                                <Shield className={styles.navIcon}/>
                                <span>Admin</span>
                            </span>

                            <ChevronDown
                                className={cn(styles.adminChevron, showAdminNavigation && styles.adminChevronOpen)}
                            />
                        </Button>

                        {showAdminNavigation && (
                            <nav
                                id="sidebar-admin-navigation"
                                className={styles.adminSubnav}
                                aria-label="Administration"
                            >
                                {adminNavigation.map(({ label, path, icon }) => (
                                    <SidebarItem
                                        key={path}
                                        label={label}
                                        to={path}
                                        icon={icon}
                                        onNavigate={onNavigate}
                                    />
                                ))}
                            </nav>
                        )}
                    </div>
                )}
            </div>
            <SidebarAccount/>
        </aside>
    );
}
