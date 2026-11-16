export const policyDetailsDialogStyles = {
    content: "flex min-w-0 flex-col gap-5",

    section: "flex flex-col gap-3",

    sectionHeader: "flex items-center justify-between gap-3",

    sectionTitle: "text-sm font-semibold text-fg",

    description: "text-sm leading-relaxed text-fg-body",

    versions: "flex flex-col gap-2",

    versionRow: [
        "flex flex-wrap items-center justify-between gap-3",
        "rounded-lg border border-border bg-surface p-3",
    ].join(" "),

    versionInfo: "flex min-w-0 flex-1 flex-col gap-1",

    versionTitle: "break-all text-sm font-medium text-fg",

    versionMeta: "text-xs text-fg-muted",

    versionStatus: "text-xs font-medium text-fg-body",

    versionActions: "flex flex-wrap items-center gap-2",

    empty: [
        "rounded-lg border border-dashed border-border",
        "px-4 py-8 text-center text-sm text-fg-muted",
    ].join(" "),

    error: "text-sm text-neg-fg",

    processingStatus: "flex items-center gap-2 text-xs text-fg-muted",
};
