import { Button } from "../button";
import { SegmentedControl } from "../segmented-control/SegmentedControl";
import { MultiSelect } from "../select/MultiSelect";
import { Select } from "../select/Select";
import { FilterDropdown } from "./FilterDropdown";
import { FilterSearch } from "./FilterSearch";
import type { CheckboxGroupFilterDefinition, FilterDefinition, FilterValue, FilterValues } from "./Filters.types";
import { filtersStyles as styles } from "./Filters.styles";

interface FiltersProps {
    definitions: FilterDefinition[];
    values: FilterValues;
    onChange: (values: FilterValues) => void;
}

export function Filters({ definitions, values, onChange }: FiltersProps) {
    const checkboxGroups = definitions.filter(
        (definition): definition is CheckboxGroupFilterDefinition =>
            definition.type === "checkboxGroup",
    );

    const hasActiveFilters = definitions.some((definition) => {
        const value = values[definition.key];

        if (Array.isArray(value)) {
            return value.length > 0;
        }

        return value !== null && value !== undefined && value !== "";
    });

    function updateValue(key: string, value: FilterValue | FilterValue[] | null) {
        onChange({
            ...values,
            [key]: value,
        });
    }

    function clearFilters() {
        const cleared: FilterValues = { ...values };

        for (const definition of definitions) {
            switch (definition.type) {
                case "search":
                    cleared[definition.key] = "";
                    break;

                case "multiSelect":
                case "checkboxGroup":
                    cleared[definition.key] = [];
                    break;

                case "select":
                case "segmentedControl":
                    cleared[definition.key] = null;
                    break;
            }
        }

        onChange(cleared);
    }

    return (
        <div className={styles.root} role="group" aria-label="Filters">
            {definitions.map((definition) => {
                const value = values[definition.key];

                switch (definition.type) {
                    case "search":
                        return (
                            <FilterSearch
                                key={definition.key}
                                value={typeof value === "string" ? value : ""}
                                onChange={(nextValue) => updateValue(definition.key, nextValue)}
                                placeholder={definition.placeholder}
                                debounceMs={definition.debounceMs}
                            />
                        );

                    case "segmentedControl":
                        return (
                            <SegmentedControl
                                key={definition.key}
                                options={definition.options}
                                value={
                                    typeof value === "string" || typeof value === "number"
                                        ? value
                                        : null
                                }
                                onChange={(selected) => updateValue(definition.key, selected)}
                                ariaLabel={definition.label ?? "Filter options"}
                            />
                        );

                    case "select":
                        return (
                            <div key={definition.key} className={styles.select}>
                                <Select
                                    options={definition.options}
                                    value={
                                        typeof value === "string" || typeof value === "number"
                                            ? value
                                            : null
                                    }
                                    onChange={(selected) => updateValue(definition.key, selected)}
                                    placeholder={definition.placeholder}
                                />
                            </div>
                        );

                    case "multiSelect":
                        return (
                            <div key={definition.key} className={styles.select}>
                                <MultiSelect
                                    options={definition.options}
                                    values={Array.isArray(value) ? value : []}
                                    onChange={(selected) => updateValue(definition.key, selected)}
                                    placeholder={definition.placeholder}
                                />
                            </div>
                        );

                    case "checkboxGroup":
                        return null;
                }
            })}

            {checkboxGroups.length > 0 && (
                <FilterDropdown
                    definitions={checkboxGroups}
                    values={values}
                    onChange={onChange}
                />
            )}

            <Button
                variant="ghost"
                size="md"
                disabled={!hasActiveFilters}
                onClick={clearFilters}
            >
                Clear filters
            </Button>
        </div>
    );
}
