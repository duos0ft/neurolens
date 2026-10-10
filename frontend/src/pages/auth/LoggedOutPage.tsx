import { Link } from "react-router";
import { Check } from "lucide-react";

import { loggedOutPageStyles as styles } from "./LoggedOutPage.styles";

export function Component() {
    return (
        <div className={styles.root}>
            <div className={styles.icon} aria-hidden="true">
                <Check size={26} strokeWidth={1.75} />
            </div>

            <div className={styles.content}>
                <h1 className={styles.title}>You're signed out</h1>

                <p className={styles.description}>
                    You've successfully signed out of NeuroLens. You can safely close this window.
                </p>
            </div>

            <Link to="/auth/login" className={styles.button}>
                Sign in again
            </Link>
        </div>
    );
}
