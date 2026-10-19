export const filterDropdownStyles = {
    root: "relative shrink-0",

    count: "rounded-md bg-muted px-1.5 py-0.5 text-xs",

    dropdown: [
        "absolute top-full left-0 z-50 mt-1 min-w-52",
        "rounded-lg border border-border bg-surface p-2 shadow-lg",
    ].join(" "),

    group: "flex flex-col gap-1 border-0 p-0",
    legend: "px-2 py-2 text-xs font-semibold text-fg-muted",

    option: [
        "flex cursor-pointer items-center gap-3 rounded-md",
        "px-2 py-2 text-sm text-fg hover:bg-muted",
        "has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-50",
    ].join(" "),

    checkbox: "size-4 accent-primary",
};
