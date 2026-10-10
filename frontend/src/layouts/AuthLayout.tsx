import { Outlet } from "react-router";

import { authLayoutStyles as styles } from "./AuthLayout.styles";

export function AuthLayout() {
    return (
        <main className={styles.root}>
            <div className={styles.content}>
                <Outlet />
            </div>
        </main>
    );
}
