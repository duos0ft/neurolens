import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "../../lib/cn";
import type { SelectProps } from "./Select.types";
import { selectStyles as styles } from "./Select.styles";

export function Select<T>({
    options,
    value,
    onChange,
    placeholder = "Select an option",
    disabled = false,
    className,
}: SelectProps<T>) {
    const [ open, setOpen ] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);
    const optionRefs = useRef<(HTMLButtonElement | null)[]>([]);

    const selectedIndex = options.findIndex((option) =>
        Object.is(option.value, value),
    );

    const selectedOption = options[selectedIndex];

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
                triggerRef.current?.focus();
            }
        }

        document.addEventListener("pointerdown", handlePointerDown);
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("pointerdown", handlePointerDown);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [ open ]);

    function selectOption(index: number) {
        onChange(index === -1 ? null : options[index].value);
        setOpen(false);
        triggerRef.current?.focus();
    }

    function handleTriggerKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
        if (disabled) return;

        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            setOpen(true);

            const enabledIndices = options
                .map((option, index) => (!option.disabled ? index : -1))
                .filter((index) => index !== -1);

            const targetIndex =
                event.key === "ArrowDown"
                    ? enabledIndices[0]
                    : enabledIndices[enabledIndices.length - 1];

            if (targetIndex !== undefined) {
                requestAnimationFrame(() => {
                    optionRefs.current[targetIndex]?.focus();
                });
            }
        }
    }

    function handleOptionKeyDown(
        event: React.KeyboardEvent<HTMLButtonElement>,
        index: number,
    ) {
        if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;

        event.preventDefault();

        const direction = event.key === "ArrowDown" ? 1 : -1;

        let nextIndex = index + direction;

        while (nextIndex >= 0 && nextIndex < options.length) {
            if (!options[nextIndex].disabled) {
                optionRefs.current[nextIndex]?.focus();
                return;
            }

            nextIndex += direction;
        }
    }

    return (
        <div ref={containerRef} className={cn(styles.wrapper, className)}>
            <button
                ref={triggerRef}
                type="button"
                disabled={disabled}
                aria-haspopup="listbox"
                aria-expanded={open}
                className={cn(styles.trigger, open && styles.triggerOpen)}
                onClick={() => setOpen((current) => !current)}
                onKeyDown={handleTriggerKeyDown}
            >
                <span className={cn(styles.value, !selectedOption && styles.placeholder)}>
                    {selectedOption?.label ?? placeholder}
                </span>

                <ChevronDown className={styles.chevron} aria-hidden="true"/>
            </button>

            {open && (
                <div className={styles.dropdown}>
                    <div role="listbox" aria-label={placeholder} className={styles.listbox}>
                        <button
                            type="button"
                            role="option"
                            aria-selected={value === null}
                            className={cn(
                                styles.option,
                                selectedIndex === -1 && styles.optionSelected,
                            )}
                            onClick={() => selectOption(-1)}
                        >
                            <span>{placeholder}</span>
                            {selectedIndex === -1 && (
                                <Check className={styles.check} aria-hidden="true"/>
                            )}
                        </button>

                        {options.map((option, index) => (
                            <button
                                key={index}
                                ref={(element) => {
                                    optionRefs.current[index] = element;
                                }}
                                type="button"
                                role="option"
                                aria-selected={selectedIndex === index}
                                disabled={option.disabled}
                                className={cn(
                                    styles.option,
                                    selectedIndex === index && styles.optionSelected,
                                )}
                                onClick={() => selectOption(index)}
                                onKeyDown={(event) => handleOptionKeyDown(event, index)}
                            >
                                <span>{option.label}</span>

                                {selectedIndex === index && (
                                    <Check className={styles.check} aria-hidden="true"/>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
