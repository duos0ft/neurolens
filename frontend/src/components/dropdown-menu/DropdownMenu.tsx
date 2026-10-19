import { type KeyboardEvent, useCallback, useEffect, useId, useRef, useState } from "react";
import { MoreHorizontal } from "lucide-react";

import { cn } from "../../lib/cn";
import { dropdownMenuStyles as styles } from "./DropdownMenu.styles";

export interface DropdownMenuItem {
    label: string;
    onSelect: () => void;
    disabled?: boolean;
    destructive?: boolean;
}

interface DropdownMenuProps {
    items: DropdownMenuItem[];
    label?: string;
    disabled?: boolean;
}

interface MenuPosition {
    top: number;
    left: number;
    maxHeight: number;
    openAbove: boolean;
}

const MENU_WIDTH = 192;
const MENU_MAX_HEIGHT = 240;
const VIEWPORT_PADDING = 8;
const MENU_GAP = 4;

export function DropdownMenu({
    items,
    label = "More actions",
    disabled = false,
}: DropdownMenuProps) {
    const menuId = useId();

    const triggerRef = useRef<HTMLButtonElement>(null);
    const popoverRef = useRef<HTMLDivElement>(null);
    const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

    const [ open, setOpen ] = useState(false);

    const [ position, setPosition ] = useState<MenuPosition>({
        top: 0,
        left: 0,
        maxHeight: MENU_MAX_HEIGHT,
        openAbove: false,
    });

    const updatePosition = useCallback(() => {
        const trigger = triggerRef.current;

        if (!trigger) {
            return;
        }

        const rect = trigger.getBoundingClientRect();

        const availableBelow =
            window.innerHeight - rect.bottom - MENU_GAP - VIEWPORT_PADDING;

        const availableAbove =
            rect.top - MENU_GAP - VIEWPORT_PADDING;

        const estimatedMenuHeight = Math.min(
            MENU_MAX_HEIGHT,
            items.length * 40 + 8,
        );

        const openAbove =
            availableBelow < estimatedMenuHeight
            && availableAbove > availableBelow;

        const availableHeight = openAbove
            ? availableAbove
            : availableBelow;

        const menuWidth = Math.min(
            MENU_WIDTH,
            window.innerWidth - VIEWPORT_PADDING * 2,
        );

        const left = Math.max(
            VIEWPORT_PADDING,
            Math.min(
                rect.right - menuWidth,
                window.innerWidth - menuWidth - VIEWPORT_PADDING,
            ),
        );

        setPosition({
            top: openAbove
                ? rect.top - MENU_GAP
                : rect.bottom + MENU_GAP,
            left,
            maxHeight: Math.max(
                0,
                Math.min(MENU_MAX_HEIGHT, availableHeight),
            ),
            openAbove,
        });
    }, [ items.length ]);

    function closeMenu(restoreFocus = true) {
        if (popoverRef.current?.matches(":popover-open")) {
            popoverRef.current.hidePopover();
        }

        setOpen(false);

        if (restoreFocus) {
            triggerRef.current?.focus();
        }
    }

    function focusItem(focusLast = false) {
        const enabledIndices = items
            .map((item, index) => !item.disabled ? index : -1)
            .filter((index) => index !== -1);

        const index = focusLast
            ? enabledIndices[enabledIndices.length - 1]
            : enabledIndices[0];

        if (index !== undefined) {
            itemRefs.current[index]?.focus();
        }
    }

    function openMenu(focusLast = false) {
        if (disabled || items.length === 0) {
            return;
        }

        updatePosition();

        if (!popoverRef.current?.matches(":popover-open")) {
            popoverRef.current?.showPopover();
        }

        setOpen(true);

        requestAnimationFrame(() => {
            focusItem(focusLast);
        });
    }

    function handleTriggerKeyDown(
        event: KeyboardEvent<HTMLButtonElement>,
    ) {
        if (
            event.key === "ArrowDown"
            || event.key === "ArrowUp"
        ) {
            event.preventDefault();
            openMenu(event.key === "ArrowUp");
        }
    }

    function handleItemKeyDown(
        event: KeyboardEvent<HTMLButtonElement>,
        index: number,
    ) {
        if (event.key === "Escape") {
            event.preventDefault();
            closeMenu();
            return;
        }

        if (event.key === "Tab") {
            closeMenu(false);
            return;
        }

        if (event.key === "Home" || event.key === "End") {
            event.preventDefault();
            focusItem(event.key === "End");
            return;
        }

        if (
            event.key !== "ArrowDown"
            && event.key !== "ArrowUp"
        ) {
            return;
        }

        event.preventDefault();

        const direction = event.key === "ArrowDown" ? 1 : -1;

        for (let step = 1; step <= items.length; step++) {
            const nextIndex =
                (index + direction * step + items.length * (step + 1))
                % items.length;

            if (!items[nextIndex].disabled) {
                itemRefs.current[nextIndex]?.focus();
                return;
            }
        }
    }

    useEffect(() => {
        if (!open) {
            return;
        }

        function handlePositionChange() {
            updatePosition();
        }

        window.addEventListener("scroll", handlePositionChange, true);
        window.addEventListener("resize", handlePositionChange);

        return () => {
            window.removeEventListener("scroll", handlePositionChange, true);
            window.removeEventListener("resize", handlePositionChange);
        };
    }, [ open, updatePosition ]);

    useEffect(() => {
        if (disabled && open) {
            closeMenu();
        }
    }, [ disabled, open ]);

    return (
        <>
            <button
                ref={triggerRef}
                type="button"
                className={styles.trigger}
                disabled={disabled || items.length === 0}
                aria-label={label}
                aria-haspopup="menu"
                aria-expanded={open}
                aria-controls={menuId}
                onClick={() => {
                    if (open) {
                        closeMenu();
                    } else {
                        openMenu();
                    }
                }}
                onKeyDown={handleTriggerKeyDown}
            >
                <MoreHorizontal
                    className="size-5"
                    aria-hidden="true"
                />
            </button>

            <div
                ref={popoverRef}
                id={menuId}
                popover="auto"
                role="menu"
                aria-label={label}
                className={styles.menu}
                style={{
                    position: "fixed",
                    inset: "auto",
                    margin: 0,
                    width: Math.min(
                        MENU_WIDTH,
                        window.innerWidth - VIEWPORT_PADDING * 2,
                    ),
                    top: position.top,
                    left: position.left,
                    maxHeight: position.maxHeight,
                    transform: position.openAbove
                        ? "translateY(-100%)"
                        : undefined,
                    overflowY: "auto",
                }}
                onToggle={(event) => {
                    if (event.newState === "closed") {
                        setOpen(false);

                        if (
                            popoverRef.current?.contains(document.activeElement)
                        ) {
                            triggerRef.current?.focus();
                        }
                    }
                }}
                onKeyDown={(event) => {
                    if (event.key === "Escape") {
                        event.preventDefault();
                        closeMenu();
                    }
                }}
            >
                {items.map((item, index) => (
                    <button
                        key={`${item.label}-${index}`}
                        ref={(element) => {
                            itemRefs.current[index] = element;
                        }}
                        type="button"
                        role="menuitem"
                        disabled={item.disabled}
                        className={cn(
                            styles.item,
                            item.destructive && styles.destructive,
                        )}
                        onClick={() => {
                            closeMenu(false);
                            item.onSelect();
                        }}
                        onKeyDown={(event) => {
                            handleItemKeyDown(event, index);
                        }}
                    >
                        {item.label}
                    </button>
                ))}
            </div>
        </>
    );
}
