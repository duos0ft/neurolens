import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, X } from "lucide-react";

import { cn } from "../../lib/cn";
import type { MultiSelectProps } from "./Select.types";
import { multiSelectStyles as styles } from "./MultiSelect.styles";

export function MultiSelect<T>({
    options,
    values,
    onChange,
    placeholder = "Select options",
    disabled = false,
    className,
}: MultiSelectProps<T>) {
    const [ open, setOpen ] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const selectedOptions = options.filter((option) =>
        values.some((value) => Object.is(value, option.value)),
    );

    useEffect(() => {
        if (!open) return;

        function handlePointerDown(event: PointerEvent) {
            if (!containerRef.current?.contains(event.target as Node)) {
                setOpen(false);
            }
        }

        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setOpen(false);
                containerRef.current?.querySelector("button")?.focus();
            }
        }

        document.addEventListener("pointerdown", handlePointerDown);
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("pointerdown", handlePointerDown);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [ open ]);

    function toggleValue(value: T) {
        const selected = values.some((item) => Object.is(item, value));

        onChange(
            selected
                ? values.filter((item) => !Object.is(item, value))
                : [ ...values, value ],
        );
    }

    return (
        <div ref={containerRef} className={cn(styles.root, className)}>
            <button
                type="button"
                className={styles.trigger}
                disabled={disabled}
                aria-expanded={open}
                aria-haspopup="true"
                onClick={() => setOpen((current) => !current)}
            >
                <span className={selectedOptions.length ? styles.value : styles.placeholder}>
                    {selectedOptions.length
                        ? `${selectedOptions.length} selected`
                        : placeholder}
                </span>

                <ChevronDown className={styles.chevron} aria-hidden="true"/>
            </button>

            {open && (
                <div className={styles.dropdown}>
                    <div className={styles.options}>
                        {options.map((option, index) => {
                            const selected = values.some((value) =>
                                Object.is(value, option.value),
                            );

                            return (
                                <label
                                    key={index}
                                    className={cn(
                                        styles.option,
                                        option.disabled && styles.optionDisabled,
                                    )}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selected}
                                        disabled={option.disabled}
                                        onChange={() => toggleValue(option.value)}
                                        className={styles.checkbox}
                                    />

                                    <span>{option.label}</span>

                                    {selected && (
                                        <Check className={styles.check} aria-hidden="true"/>
                                    )}
                                </label>
                            );
                        })}
                    </div>

                    {values.length > 0 && (
                        <button
                            type="button"
                            className={styles.clear}
                            onClick={() => onChange([])}
                        >
                            <X className="size-3.5" aria-hidden="true"/>
                            Clear selection
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
