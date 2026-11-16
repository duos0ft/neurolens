export const policySourcesStyles = {
    root: [
        "mt-5 flex min-w-0 flex-col gap-3",
        "border-t border-border pt-4",
    ].join(" "),

    heading: [
        "text-xs font-semibold",
        "text-fg-body",
    ].join(" "),

    list: "flex flex-col gap-2",

    source: [
        "flex min-w-0 items-center gap-3",
        "rounded-lg border border-border",
        "bg-surface p-3",
        "transition-colors hover:bg-muted",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    icon: [
        "flex size-9 shrink-0 items-center justify-center",
        "rounded-lg bg-accent-soft text-accent",
        "[&>svg]:size-4",
    ].join(" "),

    details: "flex min-w-0 flex-1 flex-col gap-1",

    title: [
        "truncate text-sm font-medium",
        "text-fg",
    ].join(" "),

    metadata: "text-xs text-fg-muted",

    externalIcon: "size-4 shrink-0 text-fg-muted",
};
