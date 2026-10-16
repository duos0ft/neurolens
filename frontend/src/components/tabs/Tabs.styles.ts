export const tabsStyles = {
    root: "flex w-full items-center gap-1 overflow-x-auto border-b border-border",
    tab: [
        "inline-flex shrink-0 items-center justify-center gap-2",
        "border-b-2 px-4 py-3 text-sm font-medium",
        "transition-colors",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:pointer-events-none disabled:opacity-50",
    ].join(" "),
    active: "border-primary text-fg",
    inactive: "border-transparent text-fg-muted hover:text-fg hover:border-border",
    count: "rounded-md bg-muted px-1.5 py-0.5 text-xs text-fg-muted",
    activeCount: "text-fg",
};
