import { cn } from "../../lib/cn";
import { segmentedControlStyles as styles } from "./SegmentedControl.styles";

export interface SegmentedControlOption<T> {
    label: string;
    value: T;
    disabled?: boolean;
}

export interface SegmentedControlProps<T> {
    options: SegmentedControlOption<T>[];
    value: T;
    onChange: (value: T) => void;
    className?: string;
    ariaLabel?: string;
}

export function SegmentedControl<T>({
    options,
    value,
    onChange,
    className,
    ariaLabel = "Select option",
}: SegmentedControlProps<T>) {
    return (
        <div
            className={cn(styles.root, className)}
            role="group"
            aria-label={ariaLabel}
        >
            {options.map((option, index) => {
                const selected = Object.is(option.value, value);

                return (
                    <button
                        key={index}
                        type="button"
                        disabled={option.disabled}
                        aria-pressed={selected}
                        className={cn(
                            styles.option,
                            selected ? styles.selected : styles.unselected,
                        )}
                        onClick={() => onChange(option.value)}
                    >
                        {option.label}
                    </button>
                );
            })}
        </div>
    );
}
