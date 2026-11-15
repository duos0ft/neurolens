import { forwardRef, type InputHTMLAttributes } from "react";
import { Check, Minus } from "lucide-react";

import { cn } from "../../lib/cn";
import { checkboxStyles as styles } from "./Checkbox.styles";

export interface CheckboxProps extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    "type" | "size"
> {
    label?: string;
    description?: string;
    indeterminate?: boolean;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
    function Checkbox(
        {
            label,
            description,
            indeterminate = false,
            className,
            disabled,
            id,
            ...props
        },
        ref,
    ) {
        return (
            <label
                className={cn(
                    styles.root,
                    disabled && styles.disabled,
                    className,
                )}
            >
                <span className={styles.control}>
                    <input
                        {...props}
                        ref={ref}
                        id={id}
                        type="checkbox"
                        disabled={disabled}
                        aria-checked={indeterminate ? "mixed" : undefined}
                        className={styles.input}
                    />

                    <span
                        className={styles.box}
                        aria-hidden="true"
                    >
                        {indeterminate ? (
                            <Minus className={styles.icon}/>
                        ) : (
                            <Check className={styles.icon}/>
                        )}
                    </span>
                </span>

                {(label || description) && (
                    <span className={styles.content}>
                        {label && (
                            <span className={styles.label}>
                                {label}
                            </span>
                        )}

                        {description && (
                            <span className={styles.description}>
                                {description}
                            </span>
                        )}
                    </span>
                )}
            </label>
        );
    },
);
