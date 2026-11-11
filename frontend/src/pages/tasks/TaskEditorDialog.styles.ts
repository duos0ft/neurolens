export const taskEditorDialogStyles = {
    form: [
        "flex min-w-0 flex-col gap-5",
        "max-h-[min(60dvh,520px)] overflow-y-auto",
        "pr-1",
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

    fieldGrid: "grid grid-cols-1 gap-4 sm:grid-cols-2",

    validationError: [
        "rounded-lg bg-neg-bg px-3 py-2",
        "text-sm text-neg-fg",
    ].join(" "),

    footer: "flex w-full items-center justify-end gap-2",

    subtaskSection: [
        "flex flex-col gap-3",
        "border-t border-border pt-5",
    ].join(" "),

    subtaskHeader: "flex items-start justify-between gap-3",

    subtaskHeading: "text-sm font-semibold text-fg",

    subtaskHint: "mt-1 text-xs text-fg-muted",

    emptySubtasks: "text-sm text-fg-muted",

    subtaskList: "flex flex-col gap-2",

    subtaskRow: "flex min-w-0 items-center gap-2",

    subtaskNumber: "w-5 shrink-0 text-xs text-fg-muted",

    subtaskInput: "min-w-0 flex-1",

    subtaskActions: "flex shrink-0 items-center gap-0.5",

    subtaskAction: [
        "size-8 text-fg-muted",
        "hover:text-fg",
    ].join(" "),

    removeSubtask: [
        "size-8 text-fg-muted",
        "hover:text-neg-fg",
    ].join(" "),
};
