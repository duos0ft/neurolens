export const tasksPageStyles = {
    root: "mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-8",

    description: "text-sm text-fg-muted",

    stats: "grid grid-cols-1 gap-3 sm:grid-cols-3",

    stat: "rounded-xl border border-border bg-surface p-4",

    statLabel: "text-xs text-fg-muted",

    statValue: "mt-2 text-2xl font-semibold text-fg",

    section: "flex flex-col gap-3",

    sectionHeader: "flex flex-wrap items-center justify-between gap-3",

    sectionTitle: "text-sm font-semibold text-fg",

    showingCount: "text-xs text-fg-muted",

    toolbar: [
        "flex flex-wrap items-center justify-between gap-3",
    ].join(" "),

    filters: "flex flex-wrap items-center gap-2",

    sortControl: "flex items-center gap-2",

    sortLabel: "shrink-0 text-xs text-fg-muted",

    sortSelect: "w-44",

    list: "flex flex-col gap-2",

    taskIcon: "size-5 text-fg-muted",

    taskCompletedIcon: "size-5 text-pos-fg",

    subtaskContent: "flex flex-col gap-2",

    subtaskCount: "text-xs text-fg-muted",

    subtasks: "list-disc space-y-1 pl-5 text-sm text-fg-muted",

    subtaskCompleted: "line-through opacity-60",

    empty: [
        "rounded-xl border border-border",
        "bg-surface p-8",
        "text-center text-sm text-fg-muted",
    ].join(" "),

    error: [
        "flex flex-col items-start gap-3",
        "rounded-xl border border-border",
        "bg-surface p-6",
        "text-sm text-fg-muted",
    ].join(" "),

    pagination: "flex items-center justify-center gap-3 pt-4",

    pageInfo: "text-xs text-fg-muted",
};
