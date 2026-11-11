import { type KeyboardEvent, useEffect, useId, useRef, useState } from "react";
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
    const [ position, setPosition ] = useState({
        top: 0,
        left: 0,
        width: 0,
        maxHeight: 240,
        openAbove: false,
    });

    const containerRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const optionRefs = useRef<(HTMLButtonElement | null)[]>([]);
    const listboxId = useId();

    const selectedIndex = options.findIndex((option) =>
        Object.is(option.value, value),
    );

    const selectedOption = options[selectedIndex];

    function updatePosition() {
        const trigger = triggerRef.current;
        if (!trigger) return;

        const rect = trigger.getBoundingClientRect();
        const gap = 4;
        const availableBelow = window.innerHeight - rect.bottom - gap - 8;
        const availableAbove = rect.top - gap - 8;
        const openAbove = availableBelow < 180 && availableAbove > availableBelow;
        const maxHeight = Math.max(60, Math.min(240, openAbove ? availableAbove : availableBelow));

        setPosition({
            top: openAbove ? rect.top - gap : rect.bottom + gap,
            left: rect.left,
            width: rect.width,
            maxHeight,
            openAbove,
        });
    }

    function closeDropdown() {
        dropdownRef.current?.hidePopover();
        setOpen(false);
    }

    function openDropdown(focusIndex?: number) {
        if (disabled) return;

        updatePosition();
        dropdownRef.current?.showPopover();
        setOpen(true);

        if (focusIndex !== undefined) {
            requestAnimationFrame(() => {
                optionRefs.current[focusIndex]?.focus();
            });
        }
    }

    function selectOption(index: number) {
        onChange(index === -1 ? null : options[index].value);
        closeDropdown();
        triggerRef.current?.focus();
    }

    useEffect(() => {
        if (!open) return;

        function handleScroll() {
            updatePosition();
        }

        function handleResize() {
            updatePosition();
        }

        window.addEventListener("scroll", handleScroll, true);
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("scroll", handleScroll, true);
            window.removeEventListener("resize", handleResize);
        };
    }, [ open ]);

    useEffect(() => {
        if (disabled && open) {
            closeDropdown();
        }
    }, [ disabled, open ]);

    function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
        if (disabled) return;

        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();

            const enabledIndices = options
                .map((option, index) => (!option.disabled ? index : -1))
                .filter((index) => index !== -1);

            const targetIndex = event.key === "ArrowDown"
                ? enabledIndices[0]
                : enabledIndices[enabledIndices.length - 1];

            openDropdown(targetIndex);
        }
    }

    function handleOptionKeyDown(
        event: KeyboardEvent<HTMLButtonElement>,
        index: number,
    ) {
        if (event.key === "Escape") {
            event.preventDefault();
            closeDropdown();
            triggerRef.current?.focus();
            return;
        }

        if (event.key === "Home" || event.key === "End") {
            event.preventDefault();

            const enabledIndices = options
                .map((option, optionIndex) => (!option.disabled ? optionIndex : -1))
                .filter((optionIndex) => optionIndex !== -1);

            const nextIndex = event.key === "Home"
                ? enabledIndices[0]
                : enabledIndices[enabledIndices.length - 1];

            if (nextIndex !== undefined) {
                optionRefs.current[nextIndex]?.focus();
            }

            return;
        }

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
                aria-controls={listboxId}
                aria-expanded={open}
                className={cn(styles.trigger, open && styles.triggerOpen)}
                onClick={() => {
                    if (open) {
                        closeDropdown();
                    } else {
                        openDropdown();
                    }
                }}
                onKeyDown={handleTriggerKeyDown}
            >
                <span className={cn(styles.value, !selectedOption && styles.placeholder)}>
                    {selectedOption?.label ?? placeholder}
                </span>

                <ChevronDown className={styles.chevron} aria-hidden="true"/>
            </button>

            <div
                ref={dropdownRef}
                popover="auto"
                className={styles.dropdown}
                style={{
                    position: "fixed",
                    inset: "auto",
                    margin: 0,
                    top: position.top,
                    left: position.left,
                    width: position.width,
                    maxHeight: position.maxHeight,
                    transform: position.openAbove
                        ? "translateY(-100%)"
                        : undefined,
                }}
                onToggle={(event) => {
                    if (event.newState === "closed") {
                        setOpen(false);
                    }
                }}
            >
                <div
                    id={listboxId}
                    role="listbox"
                    aria-label={placeholder}
                    className={styles.listbox}
                >

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
        </div>
    );
}
