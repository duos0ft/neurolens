import { useState } from "react";
import {
    BookOpen,
    CalendarDays,
    ChevronDown,
    ContactRound,
    ListTodo,
    MessageSquare,
    Settings,
    Shield,
    Users,
} from "lucide-react";
import { useLocation } from "react-router";

import { cn } from "../../lib/cn";
import { Button } from "../button";
import { RecentConversations } from "./RecentConversations";
import { SidebarAccount } from "./SidebarAccount";
import { SidebarItem } from "./SidebarItem";
import { sidebarStyles as styles } from "./Sidebar.styles";

const navigation = [
    { label: "Assistant", path: "/app/chat", icon: MessageSquare },
    { label: "My Tasks", path: "/app/my-tasks", icon: ListTodo },
    { label: "Calendar", path: "/calendar", icon: CalendarDays },
    { label: "Policies", path: "/policies", icon: BookOpen },
];

const adminNavigation = [
    { label: "Employees", path: "/app/admin/employees", icon: Users },
    { label: "Contact Persons", path: "/app/admin/contact-persons", icon: ContactRound },
    { label: "Settings", path: "/app/admin/settings", icon: Settings },
];

type SidebarProps = {
    isAdmin: boolean;
    mobileOpen: boolean;
    onNavigate: () => void;
};

export function Sidebar({
    isAdmin,
    mobileOpen,
    onNavigate,
}: SidebarProps) {
    const { pathname } = useLocation();

    const isAdminRoute =
        pathname === "/app/admin"
        || pathname.startsWith("/app/admin/");

    const [ adminOverride, setAdminOverride ] = useState<{
        pathname: string;
        expanded: boolean;
    } | null>(null);

    const showAdminNavigation =
        adminOverride?.pathname === pathname
            ? adminOverride.expanded
            : isAdminRoute;

    function toggleAdminNavigation() {
        setAdminOverride({
            pathname,
            expanded: !showAdminNavigation,
        });
    }

    return (
        <aside
            className={cn(
                styles.root,
                "fixed inset-y-0 left-0 z-50 w-64",
                "transition-transform duration-200 ease-in-out",
                "lg:sticky lg:top-0 lg:z-auto lg:h-dvh lg:translate-x-0",
                mobileOpen ? "translate-x-0" : "-translate-x-full",
            )}
            aria-label="Application navigation"
        >
            <div className={styles.header}>
                <div
                    className={styles.logo}
                    aria-hidden="true"
                />

                <span className={styles.brand}>
                    NeuroLens
                </span>
            </div>

            <div className={styles.content}>
                <nav
                    className={styles.nav}
                    aria-label="Main navigation"
                >
                    {navigation.map(({ label, path, icon }) => (
                        <SidebarItem
                            key={path}
                            label={label}
                            to={path}
                            icon={icon}
                            onNavigate={onNavigate}
                        />
                    ))}
                </nav>

                <div className={styles.recentSection}>
                    <RecentConversations onNavigate={onNavigate}/>
                </div>

                {isAdmin && (
                    <div className={styles.section}>
                        <Button
                            variant="ghost"
                            className={cn(
                                styles.adminToggle,
                                isAdminRoute && styles.navLinkActive,
                            )}
                            onClick={toggleAdminNavigation}
                            aria-expanded={showAdminNavigation}
                            aria-controls="sidebar-admin-navigation"
                        >
                            <span className={styles.adminToggleContent}>
                                <Shield className={styles.navIcon}/>
                                <span>Admin</span>
                            </span>

                            <ChevronDown
                                className={cn(
                                    styles.adminChevron,
                                    showAdminNavigation && styles.adminChevronOpen,
                                )}
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
