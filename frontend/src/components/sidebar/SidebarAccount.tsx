import { useEffect, useRef, useState } from "react";
import { ChevronsUpDown, LogOut, Settings, UserRound } from "lucide-react";
import { useNavigate } from "react-router";
import { Avatar } from "../avatar";
import { Button } from "../button";
import { sidebarAccountStyles as styles } from "./SidebarAccount.styles";
import { useAuth } from "../../providers/AuthProvider";

export function SidebarAccount() {
    const { employee } = useAuth();
    const navigate = useNavigate();
    const [ open, setOpen ] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);

    const displayName = employee?.display_name?.trim() || employee?.email || "My account";
    const subtitle = employee?.job_title?.trim() || (employee?.role === "admin" ? "Administrator" : "Employee");

    useEffect(() => {
        if (!open) return;

        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setOpen(false);
                triggerRef.current?.focus();
            }
        }

        function handlePointerDown(event: PointerEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setOpen(false);
            }
        }

        document.addEventListener("keydown", handleKeyDown);
        document.addEventListener("pointerdown", handlePointerDown);

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.removeEventListener("pointerdown", handlePointerDown);
        };
    }, [ open ]);

    function navigateTo(path: string) {
        setOpen(false);
        void navigate(path);
    }

    return (
        <div ref={containerRef} className={styles.root}>
            {open && (
                <div className={styles.menu} aria-label="Account options">
                    <Button variant="ghost" className={styles.menuItem} onClick={() => navigateTo("/app/profile")}>
                        <UserRound className={styles.menuIcon} />
                        My profile
                    </Button>

                    <Button variant="ghost" className={styles.menuItem} onClick={() => navigateTo("/app/preferences")}>
                        <Settings className={styles.menuIcon} />
                        Preferences
                    </Button>

                    <div className={styles.separator} />

                    <Button variant="ghost" className={styles.menuItem} onClick={() => navigateTo("/auth/logout")}>
                        <LogOut className={styles.menuIcon} />
                        Log out
                    </Button>
                </div>
            )}

            <Button
                ref={triggerRef}
                variant="ghost"
                className={styles.trigger}
                aria-expanded={open}
                aria-haspopup="menu"
                onClick={() => setOpen((value) => !value)}
            >
                <Avatar name={displayName} size="md" />

                <span className={styles.info}>
                    <span className={styles.name}>{displayName}</span>
                    <span className={styles.subtitle}>{subtitle}</span>
                </span>

                <ChevronsUpDown className={styles.chevron} />
            </Button>
        </div>
    );
}
