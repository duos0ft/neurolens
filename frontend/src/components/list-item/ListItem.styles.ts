export const listItemStyles = {
    root: [
        "flex items-start gap-3",
        "rounded-xl border border-border",
        "bg-surface p-4",
        "transition-colors duration-150",
    ].join(" "),

    selected: "border-border-strong bg-subtle",

    disabled: "opacity-50",

    leading: "mt-0.5 flex shrink-0 items-center justify-center",

    content: "flex min-w-0 flex-1 flex-col gap-2",

    heading: "flex min-w-0 items-start justify-between gap-3",

    title: "min-w-0 flex-1 text-sm font-medium text-fg",

    actions: "flex shrink-0 items-center gap-1",

    description: "text-sm leading-6 text-fg-muted",

    metadata: "flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-fg-muted",

    details: "flex flex-col gap-2",
};
