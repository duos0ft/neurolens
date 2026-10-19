export const emailInputStyles = {
    root: "w-full",
    field: [
        "flex min-h-28 w-full flex-wrap content-start items-start gap-2",
        "rounded-lg border border-border bg-surface p-3",
        "transition-colors focus-within:border-primary",
    ].join(" "),
    fieldError: "border-neg-fg",
    chip: [
        "inline-flex max-w-full items-center gap-1.5",
        "rounded-md bg-muted px-2 py-1 text-xs text-fg",
    ].join(" "),
    chipText: "max-w-64 truncate",
    remove: [
        "inline-flex size-4 items-center justify-center",
        "rounded-sm text-fg-muted hover:text-fg",
        "disabled:pointer-events-none disabled:opacity-50",
        "[&_svg]:size-3",
    ].join(" "),
    input: [
        "min-w-40 flex-1 bg-transparent py-1 text-sm text-fg",
        "outline-none placeholder:text-fg-muted",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),
    error: "mt-2 text-xs text-neg-fg",
};
