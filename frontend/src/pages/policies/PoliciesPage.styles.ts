export const policiesPageStyles = {
    root: "flex w-full flex-col gap-7",

    directory: "flex flex-col gap-4",

    policyCell: "flex min-w-0 flex-col gap-1",

    policyTitle: "font-medium text-fg",

    policyDescription: "line-clamp-2 text-xs text-fg-muted",

    category: "text-sm text-fg-body",

    date: "text-sm text-fg-muted",

    empty: [
        "flex flex-col items-center justify-center gap-3",
        "rounded-xl border border-border bg-surface",
        "px-6 py-14 text-center",
    ].join(" "),

    emptyIcon: "size-8 text-fg-muted",

    emptyTitle: "text-base font-semibold text-fg",

    emptyDescription: "max-w-md text-sm text-fg-muted",

    error: [
        "rounded-lg border border-border bg-surface",
        "px-5 py-12 text-center text-sm text-neg-fg",
    ].join(" "),
};
