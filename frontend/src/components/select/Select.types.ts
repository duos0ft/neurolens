export interface SelectOption<T> {
    label: string;
    value: T;
    disabled?: boolean;
}

export interface SelectProps<T> {
    options: SelectOption<T>[];
    value: T | null;
    onChange: (value: T | null) => void;
    placeholder?: string;
    disabled?: boolean;
    className?: string;
}

export interface MultiSelectProps<T> {
    options: SelectOption<T>[];
    values: T[];
    onChange: (values: T[]) => void;
    placeholder?: string;
    disabled?: boolean;
    className?: string;
}
