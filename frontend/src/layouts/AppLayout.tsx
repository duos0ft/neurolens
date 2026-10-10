import { Outlet } from "react-router";

import { appLayoutStyles as styles } from "./AppLayout.styles";

export function AppLayout() {
    return (
        <div className={styles.root}>
            <div className={styles.content}>
                <main className={styles.main}>
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
