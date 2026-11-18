export const sentimentAnalysisStyles = {
    root: [
        "flex items-center justify-end",
    ].join(" "),

    result: [
        "flex w-full min-w-0 max-w-md flex-col gap-3",
        "rounded-xl border border-border",
        "bg-surface px-4 py-3.5",
        "shadow-sm",
    ].join(" "),

    header: [
        "flex items-center justify-between gap-3",
    ].join(" "),

    identity: [
        "flex min-w-0 items-center gap-3",
    ].join(" "),

    iconContainer: [
        "flex size-9 shrink-0 items-center justify-center",
        "rounded-lg bg-muted",
    ].join(" "),

    icon: [
        "size-4 text-fg-soft",
    ].join(" "),

    titleGroup: [
        "flex min-w-0 flex-col gap-0.5",
    ].join(" "),

    heading: [
        "text-sm font-semibold leading-ui text-fg",
    ].join(" "),

    subtitle: [
        "text-xs text-fg-muted",
    ].join(" "),

    divider: [
        "h-px w-full bg-border",
    ].join(" "),

    confidence: [
        "flex items-center justify-between gap-3",
        "text-xs text-fg-muted",
    ].join(" "),

    confidenceValue: [
        "text-sm font-semibold tabular-nums text-fg",
    ].join(" "),

    disclaimer: [
        "flex items-start gap-2",
        "text-xs leading-relaxed text-fg-muted",
    ].join(" "),

    infoIcon: [
        "mt-0.5 size-3.5 shrink-0 text-fg-faint",
    ].join(" "),
};
