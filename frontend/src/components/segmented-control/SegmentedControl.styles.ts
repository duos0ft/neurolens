export const segmentedControlStyles = {
    root: "inline-flex h-10 max-w-full items-center gap-1 overflow-x-auto rounded-lg border border-border bg-muted p-1",
    option: [
        "flex h-full shrink-0 items-center justify-center",
        "rounded-md px-4 text-sm font-medium",
        "outline-none transition-colors",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:pointer-events-none disabled:opacity-50",
    ].join(" "),
    selected: "bg-surface text-fg shadow-sm",
    unselected: "text-fg-muted hover:bg-surface/60 hover:text-fg",
};
