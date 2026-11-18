export const sentimentAnalysisStyles = {
    root: "flex justify-end",

    result: [
        "flex w-full min-w-0 max-w-md flex-col gap-2",
        "rounded-xl border border-border bg-surface p-3",
    ].join(" "),

    header: [
        "flex items-center justify-between gap-3",
    ].join(" "),

    heading: [
        "text-sm font-semibold text-fg",
    ].join(" "),

    confidence: [
        "flex items-center justify-between gap-3",
        "text-xs text-fg-muted",
    ].join(" "),

    confidenceValue: [
        "font-medium tabular-nums text-fg",
    ].join(" "),

    disclaimer: [
        "text-xs leading-relaxed text-fg-muted",
    ].join(" "),
};
