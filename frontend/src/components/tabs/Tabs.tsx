import { cn } from "../../lib/cn";
import { tabsStyles as styles } from "./Tabs.styles";

export interface TabOption<T> {
    label: string;
    value: T;
    disabled?: boolean;
    count?: number;
}

export interface TabsProps<T> {
    options: TabOption<T>[];
    value: T;
    onChange: (value: T) => void;
    className?: string;
}

export function Tabs<T>({
    options,
    value,
    onChange,
    className,
}: TabsProps<T>) {
    return (
        <div
            className={cn(styles.root, className)}
            role="group"
            aria-label="Filter by status"
        >
            {options.map((option, index) => {
                const selected = Object.is(option.value, value);

                return (
                    <button
                        key={index}
                        type="button"
                        disabled={option.disabled}
                        aria-pressed={selected}
                        onClick={() => onChange(option.value)}
                        className={cn(
                            styles.tab,
                            selected ? styles.active : styles.inactive,
                        )}
                    >
                        {option.label}

                        {option.count !== undefined && (
                            <span
                                className={cn(
                                    styles.count,
                                    selected && styles.activeCount,
                                )}
                            >
                                {option.count}
                            </span>
                        )}
                    </button>
                );
            })}
        </div>
    );
}
