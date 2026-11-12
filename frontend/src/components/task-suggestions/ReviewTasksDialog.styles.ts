export const reviewTasksDialogStyles = {
    form: [
        "grid min-h-0 grid-cols-1 gap-5",
        "max-h-[min(60dvh,520px)] overflow-y-auto",
        "md:grid-cols-[180px_minmax(0,1fr)]",
        "md:overflow-hidden",
    ].join(" "),

    taskNavigation: [
        "flex min-w-0 gap-1 overflow-x-auto",
        "border-b border-border pb-3",
        "md:min-h-0 md:flex-col md:overflow-y-auto",
        "md:border-b-0 md:border-r md:pb-0 md:pr-3",
    ].join(" "),

    taskTab: [
        "h-auto min-h-11 min-w-[140px]",
        "justify-start gap-2 px-3 py-2.5",
        "text-left text-sm font-normal text-fg-body",
        "md:w-full md:min-w-0",
    ].join(" "),

    taskTabActive: [
        "h-auto min-h-11 min-w-[140px]",
        "justify-start gap-2 bg-muted px-3 py-2.5",
        "text-left text-sm font-medium text-fg",
        "md:w-full md:min-w-0",
    ].join(" "),

    taskNumber: [
        "flex size-6 shrink-0 items-center justify-center",
        "rounded-md bg-surface",
        "text-xs font-semibold text-fg-muted",
    ].join(" "),

    taskTabTitle: [
        "min-w-0 flex-1 truncate text-left",
    ].join(" "),

    editor: [
        "flex min-h-0 min-w-0 flex-col gap-5",
        "md:overflow-y-auto md:pr-2",
    ].join(" "),

    editorHeader: "flex items-center justify-between",

    taskIndicator: [
        "text-eyebrow font-semibold uppercase",
        "tracking-eyebrow text-fg-muted",
    ].join(" "),

    field: "flex min-w-0 flex-col gap-2",

    label: "text-sm font-medium text-fg",

    textarea: [
        "w-full min-w-0 resize-y rounded-lg",
        "border border-border bg-bg px-3 py-2.5",
        "text-sm leading-relaxed text-fg",
        "placeholder:text-fg-muted",
        "outline-none transition-colors duration-150",
        "hover:border-border-strong",
        "focus-visible:border-border-strong",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    select: [
        "h-10 w-full min-w-0 rounded-lg",
        "border border-border bg-bg px-3",
        "text-sm text-fg",
        "outline-none transition-colors duration-150",
        "hover:border-border-strong",
        "focus-visible:border-border-strong",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    fieldGrid: [
        "grid grid-cols-1 gap-4 sm:grid-cols-2",
    ].join(" "),

    subtaskSection: [
        "flex flex-col gap-3",
        "border-t border-border pt-5",
    ].join(" "),

    subtaskHeader: [
        "flex items-start justify-between gap-3",
    ].join(" "),

    subtaskHeading: "text-sm font-semibold text-fg",

    subtaskHint: "mt-1 text-xs text-fg-muted",

    emptySubtasks: "text-sm text-fg-muted",

    subtaskList: "flex flex-col gap-2",

    subtaskRow: [
        "flex min-w-0 items-center gap-2",
        "[&_input]:min-w-0 [&_input]:flex-1",
    ].join(" "),

    subtaskNumber: "w-5 shrink-0 text-xs text-fg-muted",

    removeSubtask: [
        "shrink-0 text-fg-muted",
        "hover:text-neg-fg",
    ].join(" "),

    validationError: [
        "rounded-lg bg-neg-bg px-3 py-2",
        "text-sm text-neg-fg",
    ].join(" "),

    footer: [
        "flex w-full flex-wrap items-center",
        "justify-between gap-3",
    ].join(" "),

    footerCount: "text-sm text-fg-muted",

    footerActions: "flex items-center gap-2",

    deadlineSection: [
        "flex min-w-0 flex-col gap-3",
    ].join(" "),

    deadlineHeader: [
        "flex items-center justify-between gap-3",
    ].join(" "),

    deadlineHeading: [
        "text-sm font-semibold text-fg",
    ].join(" "),

    deadlineHint: [
        "text-xs leading-5 text-fg-muted",
    ].join(" "),

};
