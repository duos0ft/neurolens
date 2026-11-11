export const taskSuggestionsStyles = {
    root: "mt-4 flex flex-col gap-3",

    header: "flex items-center justify-between gap-3",

    title: "text-sm font-semibold text-fg",

    count: "text-xs text-fg-muted",

    description: "text-sm text-fg-muted",

    list: "flex flex-col gap-2",

    item: [
        "flex items-start gap-3",
        "rounded-xl border border-border",
        "bg-surface p-4",
    ].join(" "),

    itemSaved: [
        "border-border bg-subtle",
    ].join(" "),

    checkbox: [
        "mt-1 size-4 shrink-0 accent-primary",
        "cursor-pointer",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    savedIcon: "mt-0.5 size-4 shrink-0 text-pos-fg",

    itemContent: "flex min-w-0 flex-1 flex-col gap-1.5",

    itemHeading: "flex min-w-0 flex-col items-start gap-1",

    itemTitle: "text-sm font-medium text-fg",

    savedLabel: "text-xs font-medium text-pos-fg",

    itemDescription: "text-sm leading-6 text-fg-muted",

    metadata: "flex flex-wrap items-center gap-3 text-xs text-fg-muted",

    subtasks: "list-disc space-y-1 pl-5 text-sm text-fg-muted",

    footer: "flex flex-wrap items-center justify-between gap-3 pt-2",

    selectedCount: "text-xs text-fg-muted",

    empty: "rounded-xl border border-border p-4 text-sm text-fg-muted",
    
    archivedIcon: "mt-0.5 size-4 shrink-0 text-fg-muted",

    removedIcon: "mt-0.5 size-4 shrink-0 text-fg-muted",

    inactiveLabel: "text-fg-muted",
};
