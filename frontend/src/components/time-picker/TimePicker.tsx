import { type KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";
import ReactDatePicker from "react-datepicker";
import { Clock3 } from "lucide-react";

import { Input } from "../input";

import "react-datepicker/dist/react-datepicker.css";
import "./TimePicker.css";

interface TimePickerProps {
    value: string | null;
    onChange: (value: string | null) => void;
    disabled?: boolean;
    clearable?: boolean;
    id?: string;
    interval?: number;
}

const POPUP_WIDTH = 184;
const POPUP_HEIGHT = 270;
const POPUP_GAP = 6;

function isValidTime(value: string): boolean {
    return /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
}

function parseTime(value: string | null): Date | null {
    if (!value || !isValidTime(value)) {
        return null;
    }

    const [ hours, minutes ] = value.split(":").map(Number);

    return new Date(2000, 0, 1, hours, minutes);
}

function formatTime(value: Date | null): string | null {
    if (!value) {
        return null;
    }

    const hours = String(value.getHours()).padStart(2, "0");
    const minutes = String(value.getMinutes()).padStart(2, "0");

    return `${hours}:${minutes}`;
}

export function TimePicker({
    value,
    onChange,
    disabled = false,
    clearable = false,
    id,
    interval = 15,
}: TimePickerProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const popoverRef = useRef<HTMLDivElement>(null);

    const [ draft, setDraft ] = useState(value ?? "");
    const [ open, setOpen ] = useState(false);
    const [ invalid, setInvalid ] = useState(false);

    const [ position, setPosition ] = useState({
        top: 0,
        left: 0,
    });

    useEffect(() => {
        setDraft(value ?? "");
        setInvalid(false);
    }, [ value ]);

    const updatePosition = useCallback(() => {
        const input = inputRef.current;

        if (!input) {
            return;
        }

        const rect = input.getBoundingClientRect();

        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;

        const openAbove =
            spaceBelow < POPUP_HEIGHT + POPUP_GAP
            && spaceAbove > spaceBelow;

        const top = openAbove
            ? Math.max(
                8,
                rect.top - POPUP_HEIGHT - POPUP_GAP,
            )
            : Math.min(
                rect.bottom + POPUP_GAP,
                window.innerHeight - POPUP_HEIGHT - 8,
            );

        const left = Math.max(
            8,
            Math.min(
                rect.left,
                window.innerWidth - POPUP_WIDTH - 8,
            ),
        );

        setPosition({ top, left });
    }, []);

    function closePopover() {
        popoverRef.current?.hidePopover();
        setOpen(false);
    }

    function openPopover() {
        if (disabled) {
            return;
        }

        updatePosition();
        popoverRef.current?.showPopover();
        setOpen(true);
    }

    function togglePopover() {
        if (open) {
            closePopover();
        } else {
            openPopover();
        }
    }

    function commitTime(): boolean {
        const normalized = draft.trim();

        if (!normalized && clearable) {
            setInvalid(false);
            onChange(null);
            return true;
        }

        if (!isValidTime(normalized)) {
            setInvalid(true);
            return false;
        }

        setDraft(normalized);
        setInvalid(false);

        if (normalized !== value) {
            onChange(normalized);
        }

        return true;
    }

    function handleKeyDown(
        event: KeyboardEvent<HTMLInputElement>,
    ) {
        if (event.key === "Enter") {
            event.preventDefault();
            commitTime();
            return;
        }

        if (event.key === "Escape") {
            event.preventDefault();
            setDraft(value ?? "");
            setInvalid(false);
            closePopover();
            return;
        }

        if (event.key === "ArrowDown" && !open) {
            event.preventDefault();
            openPopover();
        }
    }

    useEffect(() => {
        if (!open) {
            return;
        }

        function reposition() {
            updatePosition();
        }

        window.addEventListener("resize", reposition);
        window.addEventListener("scroll", reposition, true);

        return () => {
            window.removeEventListener("resize", reposition);
            window.removeEventListener("scroll", reposition, true);
        };
    }, [ open, updatePosition ]);

    useEffect(() => {
        if (disabled && open) {
            closePopover();
        }
    }, [ disabled, open ]);

    return (
        <div className="neurolens-time-picker relative w-full min-w-0">
            <Input
                ref={inputRef}
                id={id}
                type="text"
                inputSize="md"
                value={draft}
                onChange={(event) => {
                    setDraft(event.target.value);
                    setInvalid(false);
                }}
                onBlur={commitTime}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                placeholder="HH:mm"
                maxLength={5}
                inputMode="numeric"
                autoComplete="off"
                aria-invalid={invalid}
                aria-label="Time in 24-hour format"
                aria-describedby={
                    invalid && id
                        ? `${id}-error`
                        : undefined
                }
                className="pr-11"
            />

            <button
                type="button"
                disabled={disabled}
                onClick={togglePopover}
                aria-label="Choose time"
                aria-haspopup="dialog"
                aria-expanded={open}
                className={[
                    "absolute right-0 top-0",
                    "flex h-10 w-10 items-center justify-center",
                    "rounded-r-lg text-fg-muted",
                    "transition-colors hover:text-fg",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                    "focus-visible:outline-2 focus-visible:outline-ring",
                ].join(" ")}
            >
                <Clock3
                    className="size-4"
                    aria-hidden="true"
                />
            </button>

            {invalid && (
                <p
                    id={id ? `${id}-error` : undefined}
                    className="mt-1 text-xs text-neg-fg"
                    role="alert"
                >
                    Enter a valid time (00:00–23:59).
                </p>
            )}

            <div
                ref={popoverRef}
                popover="auto"
                className="neurolens-time-popover"
                style={{
                    position: "fixed",
                    inset: "auto",
                    margin: 0,
                    top: position.top,
                    left: position.left,
                    width: POPUP_WIDTH,
                }}
                onToggle={(event) => {
                    setOpen(event.newState === "open");
                }}
            >
                <ReactDatePicker
                    inline
                    selected={parseTime(value)}
                    onChange={(date: Date | null) => {
                        const formatted = formatTime(date);

                        setDraft(formatted ?? "");
                        setInvalid(false);
                        onChange(formatted);

                        closePopover();
                        inputRef.current?.focus();
                    }}
                    showTimeSelect
                    showTimeSelectOnly
                    timeIntervals={interval}
                    timeFormat="h:mm aa"
                    timeCaption="Time"
                    dateFormat="h:mm aa"
                    calendarClassName="neurolens-time-calendar"
                />
            </div>
        </div>
    );
}
