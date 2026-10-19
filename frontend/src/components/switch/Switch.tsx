import { cn } from "../../lib/cn";
import type { SwitchProps } from "./Switch.types";
import { switchStyles as styles } from "./Switch.styles";

export function Switch({
    id,
    checked,
    onChange,
    disabled = false,
    className,
    "aria-label": ariaLabel,
    "aria-describedby": ariaDescribedBy,
}: SwitchProps) {
    return (
        <button
            id={id}
            type="button"
            role="switch"
            aria-checked={checked}
            aria-label={ariaLabel}
            aria-describedby={ariaDescribedBy}
            disabled={disabled}
            data-checked={checked}
            className={cn(styles.root, "group", className)}
            onClick={() => onChange(!checked)}
        >
            <span className={styles.thumb} aria-hidden="true"/>
        </button>
    );
}
