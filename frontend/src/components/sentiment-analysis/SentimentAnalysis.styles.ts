export const sentimentAnalysisStyles = {
    root: "flex justify-end",

    result: [
        "flex w-full min-w-0 max-w-md flex-col gap-3",
        "rounded-xl border border-border",
        "bg-surface px-4 py-3",
    ].join(" "),

    header: [
        "flex items-center justify-between gap-3",
    ].join(" "),

    title: [
        "flex items-center gap-2",
        "text-xs font-semibold text-fg",
    ].join(" "),

    icon: "size-4 text-fg-muted",

    details: [
        "flex items-center justify-between gap-3",
    ].join(" "),

    detailLabel: "text-xs text-fg-muted",

    confidenceValue: [
        "text-xs font-semibold tabular-nums text-fg",
    ].join(" "),

    disclaimer: [
        "border-t border-border pt-3",
        "text-xs leading-relaxed text-fg-muted",
    ].join(" "),
};
