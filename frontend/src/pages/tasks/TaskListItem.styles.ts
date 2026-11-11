export const taskListItemStyles = {
    statusIcon: "size-5 text-fg-muted",

    completedIcon: "size-5 text-pos-fg",

    statusButton: [
        "flex size-6 shrink-0 items-center justify-center",
        "rounded-full transition-colors duration-150",
        "cursor-pointer hover:bg-muted",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    subtaskContent: "flex flex-col gap-3 pt-2",

    subtaskHeader: "flex items-center justify-between gap-3",

    subtaskCount: "text-xs text-fg-muted",

    progressTrack: "h-1.5 w-full overflow-hidden rounded-full bg-muted",

    progressFill: "h-full rounded-full bg-primary transition-all duration-200",

    subtasks: "flex flex-col gap-2",

    subtaskRow: "flex min-w-0 items-start gap-3",

    subtaskCheckbox: [
        "mt-0.5 size-4 shrink-0 accent-primary",
        "cursor-pointer",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    subtaskTitle: "min-w-0 text-sm text-fg-body",

    subtaskCompleted: "min-w-0 text-sm text-fg-muted line-through",
};
