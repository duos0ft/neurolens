export const selectStyles = {
    wrapper: "relative w-full min-w-0",

    trigger: [
        "flex h-10 w-full min-w-0 items-center justify-between gap-2",
        "rounded-lg border border-border bg-bg px-3",
        "text-left text-sm text-fg",
        "outline-none transition-colors duration-150",
        "hover:border-border-strong",
        "focus-visible:border-border-strong",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    triggerOpen: [
        "border-border-strong",
    ].join(" "),

    value: "min-w-0 flex-1 truncate",

    placeholder: "text-fg-muted",

    chevron: [
        "size-4 shrink-0 text-fg-muted",
    ].join(" "),

    dropdown: [
        "m-0 overflow-hidden rounded-xl",
        "border border-border bg-surface",
        "p-1.5 text-fg shadow-popover",
        "outline-none",
    ].join(" "),

    listbox: [
        "flex max-h-full flex-col gap-1 overflow-y-auto",
    ].join(" "),

    option: [
        "flex min-h-9 w-full items-center justify-between gap-3",
        "rounded-lg px-3 py-2",
        "text-left text-sm text-fg-body",
        "outline-none transition-colors duration-150",
        "hover:bg-muted hover:text-fg",
        "focus-visible:bg-muted focus-visible:text-fg",
        "disabled:cursor-not-allowed disabled:opacity-40",
    ].join(" "),

    optionSelected: [
        "bg-muted font-medium text-fg",
    ].join(" "),

    check: "size-4 shrink-0 text-fg",
};
