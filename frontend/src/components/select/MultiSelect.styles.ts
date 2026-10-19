export const multiSelectStyles = {
    root: "relative w-full",
    trigger: [
        "flex h-10 w-full items-center justify-between gap-2",
        "rounded-md border border-border bg-surface px-3",
        "text-left text-sm text-fg",
        "outline-none focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),
    value: "truncate text-fg",
    placeholder: "truncate text-fg-muted",
    chevron: "size-4 shrink-0 text-fg-muted",
    dropdown: [
        "absolute top-full right-0 left-0 z-50 mt-1",
        "overflow-hidden rounded-md border border-border",
        "bg-surface shadow-lg",
    ].join(" "),
    options: "max-h-60 overflow-y-auto p-1",
    option: "flex cursor-pointer items-center gap-2 rounded-sm px-3 py-2 text-sm text-fg hover:bg-muted focus-within:bg-muted",
    optionDisabled: "cursor-not-allowed opacity-50",
    checkbox: "size-4 accent-primary",
    check: "ml-auto size-4 text-primary",
    clear: "flex w-full items-center justify-center gap-2 border-t border-border px-3 py-2 text-xs text-fg-muted hover:bg-muted",
};
