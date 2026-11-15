export const suggestedClarificationsStyles = {
    root: [
        "flex min-w-0 flex-col gap-3",
        "rounded-xl border border-border bg-surface p-4",
    ].join(" "),

    header: "flex items-start gap-3",

    iconContainer: [
        "flex size-8 shrink-0 items-center justify-center",
        "rounded-lg bg-accent-soft text-accent",
    ].join(" "),

    icon: "size-4",

    headerContent: "flex min-w-0 flex-1 flex-col gap-1",

    title: "text-sm font-semibold text-fg",

    description: "text-xs leading-relaxed text-fg-muted",

    questions: "flex flex-col gap-2",

    questionRow: [
        "flex min-w-0 items-start gap-2.5",
    ].join(" "),

    questionCheckbox: [
        "flex h-10 shrink-0 items-center",
    ].join(" "),

    questionInput: [
        "min-h-10 w-full min-w-0 resize-none",
        "rounded-md border border-border bg-bg",
        "px-3 py-2.5",
        "text-sm leading-5 text-fg",
        "outline-none transition-colors duration-150",
        "hover:border-border-strong",
        "focus-visible:border-border-strong",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "overflow-hidden",
    ].join(" "),

    footer: [
        "flex flex-wrap items-center justify-between gap-3",
        "border-t border-border pt-3",
    ].join(" "),

    selectedCount: "text-xs text-fg-muted",

    actions: "flex items-center gap-2",

    error: "text-xs text-neg-fg",
};
