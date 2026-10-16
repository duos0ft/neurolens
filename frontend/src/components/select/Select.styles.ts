export const selectStyles = {
    wrapper: "relative w-full",

    trigger: [
        "flex h-10 w-full items-center justify-between gap-2",
        "rounded-md border border-border bg-surface px-3",
        "text-left text-sm text-fg",
        "outline-none transition-colors",
        "hover:border-fg-muted/40",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    triggerOpen: "border-primary",

    value: "truncate",
    placeholder: "text-fg-muted",
    chevron: "size-4 shrink-0 text-fg-muted",

    dropdown: [
        "absolute top-full left-0 z-50 mt-1 w-full min-w-max",
        "rounded-md border border-border bg-surface",
        "p-1 shadow-lg",
    ].join(" "),

    listbox: "max-h-60 overflow-y-auto",

    option: [
        "flex w-full items-center justify-between gap-3",
        "rounded-sm px-3 py-2 text-left text-sm text-fg",
        "outline-none transition-colors",
        "hover:bg-muted focus-visible:bg-muted",
        "disabled:cursor-not-allowed disabled:opacity-40",
    ].join(" "),

    optionSelected: "bg-muted font-medium",
    check: "size-4 shrink-0 text-primary",
};
