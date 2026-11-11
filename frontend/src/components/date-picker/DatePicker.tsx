import { forwardRef, type InputHTMLAttributes } from "react";
import ReactDatePicker from "react-datepicker";
import { CalendarDays } from "lucide-react";

import { Input } from "../input";

import "react-datepicker/dist/react-datepicker.css";
import "./DatePicker.css";

interface DatePickerProps {
    value: string | null;
    onChange: (value: string | null) => void;
    disabled?: boolean;
    id?: string;
}

function parseDate(value: string | null): Date | null {
    if (!value) {
        return null;
    }

    const [ year, month, day ] = value.split("-").map(Number);

    if (
        !Number.isInteger(year)
        || !Number.isInteger(month)
        || !Number.isInteger(day)
    ) {
        return null;
    }

    const date = new Date(year, month - 1, day);

    if (
        date.getFullYear() !== year
        || date.getMonth() !== month - 1
        || date.getDate() !== day
    ) {
        return null;
    }

    return date;
}

function formatDate(date: Date | null): string | null {
    if (!date) {
        return null;
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

const DatePickerInput = forwardRef<
    HTMLInputElement,
    InputHTMLAttributes<HTMLInputElement>
>((props, ref) => (
    <Input
        {...props}
        ref={ref}
        inputSize="md"
        readOnly
        className="cursor-pointer pr-10"
    />
));

DatePickerInput.displayName = "DatePickerInput";

export function DatePicker({
    value,
    onChange,
    disabled = false,
    id,
}: DatePickerProps) {
    return (
        <div className="relative w-full min-w-0">
            <ReactDatePicker
                id={id}
                selected={parseDate(value)}
                onChange={(date: Date | null) => {
                    onChange(formatDate(date));
                }}
                dateFormat="dd MMM yyyy"
                placeholderText="Choose a date"
                disabled={disabled}
                isClearable
                showPopperArrow={false}
                popperPlacement="top-start"
                customInput={<DatePickerInput/>}
                calendarClassName="neurolens-calendar"
                wrapperClassName="w-full"
            />

            <CalendarDays
                className={[
                    "pointer-events-none absolute right-3 top-1/2",
                    "size-4 -translate-y-1/2 text-fg-muted",
                ].join(" ")}
                aria-hidden="true"
            />
        </div>
    );
}
