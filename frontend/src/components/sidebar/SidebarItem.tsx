import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router";

import { cn } from "../../lib/cn";
import { sidebarItemStyles as styles } from "./SidebarItem.styles";

type SidebarItemProps = {
    label: string;
    to: string;
    icon: LucideIcon;
    count?: number;
    collapsed?: boolean;
    onNavigate?: () => void;
};

export function SidebarItem({ label, to, icon: Icon, count, collapsed = false, onNavigate }: SidebarItemProps) {
    return (
        <NavLink
            to={to}
            end
            onClick={onNavigate}
            title={collapsed ? label : undefined}
            className={({ isActive }) => cn(styles.root, isActive && styles.active, collapsed && styles.collapsed)}
        >
            {({ isActive }) => (
                <>
                    <Icon className={cn(styles.icon, isActive && styles.iconActive)} />

                    <span className={cn(styles.label, collapsed && "lg:hidden")}>{label}</span>

                    {count !== undefined && !collapsed && <span className={styles.count}>{count}</span>}
                </>
            )}
        </NavLink>
    );
}
