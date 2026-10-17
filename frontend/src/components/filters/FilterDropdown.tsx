import { useEffect, useRef, useState } from "react";
import { ChevronDown, ListFilter } from "lucide-react";

import { Button } from "../button";
import type { CheckboxGroupFilterDefinition, FilterValue, FilterValues } from "./Filters.types";
import { filterDropdownStyles as styles } from "./FilterDropdown.styles";

interface FilterDropdownProps {
    definitions: CheckboxGroupFilterDefinition[];
    values: FilterValues;
    onChange: (values: FilterValues) => void;
}

export function FilterDropdown({
    definitions,
    values,
    onChange,
}: FilterDropdownProps) {
    const [ open, setOpen ] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);

    const selectedCount = definitions.reduce((total, definition) => {
        const selected = values[definition.key];
        return total + (Array.isArray(selected) ? selected.length : 0);
    }, 0);

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

    function toggleOption(key: string, option: FilterValue) {
        const current = values[key];
        const selected = Array.isArray(current) ? current : [];

        onChange({
            ...values,
            [key]: selected.includes(option)
                ? selected.filter((value) => value !== option)
                : [ ...selected, option ],
        });
    }

    return (
        <div ref={containerRef} className={styles.root}>
            <Button
                ref={triggerRef}
                variant="secondary"
                size="md"
                aria-expanded={open}
                aria-haspopup="true"
                onClick={() => setOpen((current) => !current)}
            >
                <ListFilter aria-hidden="true"/>
                Filters

                {selectedCount > 0 && (
                    <span className={styles.count}>{selectedCount}</span>
                )}

                <ChevronDown aria-hidden="true"/>
            </Button>

            {open && (
                <div className={styles.dropdown}>
                    {definitions.map((definition) => {
                        const current = values[definition.key];
                        const selected = Array.isArray(current) ? current : [];

                        return (
                            <fieldset key={definition.key} className={styles.group}>
                                <legend className={styles.legend}>
                                    {definition.label}
                                </legend>

                                {definition.options.map((option) => (
                                    <label
                                        key={String(option.value)}
                                        className={styles.option}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selected.includes(option.value)}
                                            disabled={option.disabled}
                                            onChange={() =>
                                                toggleOption(definition.key, option.value)
                                            }
                                            className={styles.checkbox}
                                        />

                                        <span>{option.label}</span>
                                    </label>
                                ))}
                            </fieldset>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
