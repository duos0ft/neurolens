import type { SelectOption } from "../select/Select.types";

export type FilterValue = string | number;

export interface SearchFilterDefinition {
    key: string;
    type: "search";
    placeholder?: string;
    debounceMs?: number;
}

export interface SelectFilterDefinition<T extends FilterValue = FilterValue> {
    key: string;
    type: "select";
    placeholder?: string;
    options: SelectOption<T>[];
}

export interface MultiSelectFilterDefinition<T extends FilterValue = FilterValue> {
    key: string;
    type: "multiSelect";
    label: string;
    placeholder?: string;
    options: SelectOption<T>[];
}

export interface SegmentedControlFilterDefinition {
    key: string;
    type: "segmentedControl";
    label?: string;
    options: SelectOption<FilterValue | null>[];
}

export interface CheckboxGroupFilterDefinition<T extends FilterValue = FilterValue> {
    key: string;
    type: "checkboxGroup";
    label: string;
    options: SelectOption<T>[];
}

export type FilterDefinition =
    | SearchFilterDefinition
    | SelectFilterDefinition
    | MultiSelectFilterDefinition
    | SegmentedControlFilterDefinition
    | CheckboxGroupFilterDefinition;

export type FilterValues = Record<string, FilterValue | FilterValue[] | null>;
