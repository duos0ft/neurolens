import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { Input } from "../input";
import { filtersStyles as styles } from "./Filters.styles";

interface FilterSearchProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    debounceMs?: number;
}

export function FilterSearch({
    value,
    onChange,
    placeholder = "Search...",
    debounceMs = 300,
}: FilterSearchProps) {
    const [ inputValue, setInputValue ] = useState(value);

    useEffect(() => {
        setInputValue(value);
    }, [ value ]);

    useEffect(() => {
        if (inputValue === value) return;

        const timeout = window.setTimeout(() => {
            onChange(inputValue.trim());
        }, debounceMs);

        return () => window.clearTimeout(timeout);
    }, [ inputValue, value, debounceMs, onChange ]);

    return (
        <div className={styles.search}>
            <Search className={styles.searchIcon} aria-hidden="true"/>

            <Input
                type="search"
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                placeholder={placeholder}
                aria-label={placeholder}
                className={styles.searchInput}
            />
        </div>
    );
}
