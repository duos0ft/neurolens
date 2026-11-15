export const calendarEventDetailsDialogStyles = {
    root: "flex flex-col gap-5",

    heading: "flex min-w-0 items-start gap-3",

    iconContainer: [
        "flex size-10 shrink-0 items-center justify-center",
        "rounded-lg",
    ].join(" "),

    icon: "size-5",

    headingContent: "flex min-w-0 flex-1 flex-col gap-1",

    title: [
        "text-base font-semibold leading-snug",
        "break-words text-fg",
    ].join(" "),

    eventType: "text-xs font-medium text-fg-muted",

    details: [
        "flex flex-col gap-4",
        "border-t border-border pt-4",
    ].join(" "),

    detailRow: "flex min-w-0 items-start gap-3",

    detailIcon: "mt-0.5 size-4 shrink-0 text-fg-muted",

    detailContent: "flex min-w-0 flex-col gap-1",

    detailLabel: "text-xs text-fg-muted",

    detailValue: "text-sm leading-relaxed text-fg-body",

    descriptionSection: [
        "flex flex-col gap-2",
        "border-t border-border pt-4",
    ].join(" "),

    descriptionHeading: "text-sm font-medium text-fg",

    description: [
        "whitespace-pre-wrap break-words",
        "text-sm leading-relaxed text-fg-body",
    ].join(" "),

    footer: "flex w-full items-center justify-end gap-2",

    eventTypes: {
        task_deadline: "bg-blue-50 dark:bg-blue-500/10",
        meeting: "bg-violet-50 dark:bg-violet-500/10",
        appointment: "bg-teal-50 dark:bg-teal-500/10",
        event: "bg-slate-50 dark:bg-slate-500/10",
        deadline: "bg-amber-50 dark:bg-amber-500/10",
    },

    iconTypes: {
        task_deadline: "text-blue-600 dark:text-blue-400",
        meeting: "text-violet-600 dark:text-violet-400",
        appointment: "text-teal-600 dark:text-teal-400",
        event: "text-slate-500 dark:text-slate-400",
        deadline: "text-amber-600 dark:text-amber-400",
    },

    completedTitle: "text-fg-muted line-through",
};
