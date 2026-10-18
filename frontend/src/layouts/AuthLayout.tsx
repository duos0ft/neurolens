import type { PropsWithChildren } from "react";
import { Outlet } from "react-router";

import { authLayoutStyles as styles } from "./AuthLayout.styles";

export function AuthLayout({ children }: PropsWithChildren) {
    return (
        <main className={styles.root}>
            <div className={styles.content}>
                {children ?? <Outlet/>}
            </div>
        </main>
    );
}
