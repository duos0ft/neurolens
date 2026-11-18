import { chatThinkingIndicatorStyles as styles } from "./ChatThinkingIndicator.styles";

export function ChatThinkingIndicator() {
    return (
        <div
            className={styles.root}
            role="status"
            aria-label="NeuroLens is generating a response"
            aria-live="polite"
        >
            <div className={styles.orb} aria-hidden="true"/>

            <div className={styles.content}>
                <span className={styles.label}>
                    NeuroLens
                </span>

                <span className={styles.status}>
                    Thinking…
                </span>

                <div className={styles.skeleton} aria-hidden="true">
                    <div className={styles.skeletonLong}/>
                    <div className={styles.skeletonShort}/>
                </div>
            </div>
        </div>
    );
}
