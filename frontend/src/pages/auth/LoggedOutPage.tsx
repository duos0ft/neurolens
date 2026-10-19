import { ArrowRight, CircleCheck } from "lucide-react";
import { useNavigate } from "react-router";

import { Button } from "../../components/button";
import { Card } from "../../components/card";
import { cn } from "../../lib/cn";
import { authResultStyles as styles } from "./AuthResult.styles";

export function Component() {
    const navigate = useNavigate();

    return (
        <div className={styles.root}>
            <Card variant="flat" padding="lg" className={styles.card}>
                <div className={cn(styles.icon, styles.successIcon)} aria-hidden="true">
                    <CircleCheck className={styles.iconSvg} strokeWidth={1.75} />
                </div>

                <div className={styles.content}>
                    <h1 className={styles.title}>You're signed out</h1>
                    <p className={styles.description}>Your NeuroLens session has ended securely.</p>
                </div>
                <Button variant="primary" size="md" className={styles.action} onClick={() => navigate("/auth/login")}>
                    Sign in again
                    <ArrowRight />
                </Button>
            </Card>
        </div>
    );
}
