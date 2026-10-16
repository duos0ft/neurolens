import { SegmentedControl } from "../segmented-control/SegmentedControl";
import { MultiSelect } from "../select/MultiSelect";
import { Select } from "../select/Select";
import { FilterSearch } from "./FilterSearch";
import type { FilterDefinition, FilterValue, FilterValues } from "./Filters.types";
import { filtersStyles as styles } from "./Filters.styles";

interface FiltersProps {
    definitions: FilterDefinition[];
    values: FilterValues;
    onChange: (values: FilterValues) => void;
}

export function Filters({ definitions, values, onChange }: FiltersProps) {
    function updateValue(key: string, value: FilterValue | FilterValue[] | null) {
        onChange({
            ...values,
            [key]: value,
        });
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
                }
            })}
        </div>
    );
}
