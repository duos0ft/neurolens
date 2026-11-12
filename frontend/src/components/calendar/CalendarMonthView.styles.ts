export const calendarMonthViewStyles = {
    root: [
        "min-w-0 overflow-hidden rounded-xl",
        "border border-border bg-surface",
    ].join(" "),

    scroll: "overflow-x-auto",

    content: "min-w-[770px]",

    weekdays: [
        "grid grid-cols-7",
        "border-b border-border bg-surface",
    ].join(" "),

    weekday: [
        "px-3 py-3 text-center",
        "text-xs font-medium text-fg-muted",
    ].join(" "),

    weeks: "flex flex-col gap-px bg-border",

    week: "grid grid-cols-7 gap-px",

    day: [
        "flex min-h-[126px] min-w-0 flex-col gap-2",
        "bg-surface px-2 py-2.5",
    ].join(" "),

    dayOutside: "bg-surface",

    dayToday: "bg-surface",

    dayHeader: "flex items-center justify-between",

    dayButton: [
        "flex size-7 shrink-0 items-center justify-center",
        "rounded-md text-xs font-medium text-fg",
        "transition-colors duration-150",
        "hover:bg-muted",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    dayButtonOutside: "text-fg-faint",

    dayButtonToday: [
        "rounded-full bg-accent font-semibold text-white",
        "hover:bg-accent-hover",
    ].join(" "),

    dayEvents: "flex min-w-0 flex-col gap-1",

    event: [
        "flex w-full min-w-0 items-start gap-1.5",
        "rounded-[4px] border-l-[3px]",
        "px-2 py-1.5 text-left",
        "transition-colors duration-150",
        "hover:brightness-95",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    eventIcon: "mt-0.5 size-3 shrink-0",

    eventContent: "flex min-w-0 flex-1 flex-col gap-0.5",

    eventTitle: [
        "line-clamp-2 text-[11px] font-medium",
        "leading-[1.4] text-fg",
        "break-words",
    ].join(" "),

    eventTime: [
        "text-[10px] tabular-nums text-fg-muted",
    ].join(" "),

    eventCompleted: [
        "border-l-border-strong! bg-muted/60!",
        "opacity-65",
    ].join(" "),

    eventCompletedTitle: [
        "text-fg-muted line-through",
    ].join(" "),

    eventCompletedIcon: "text-fg-muted!",

    moreButton: [
        "self-start rounded px-2 py-1",
        "text-xs font-medium text-fg-muted",
        "transition-colors duration-150",
        "hover:bg-muted hover:text-fg",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    eventTypes: {
        task_deadline: [
            "border-l-blue-600 bg-blue-50",
            "dark:border-l-blue-400 dark:bg-blue-500/10",
        ].join(" "),

        meeting: [
            "border-l-violet-600 bg-violet-50",
            "dark:border-l-violet-400 dark:bg-violet-500/10",
        ].join(" "),

        appointment: [
            "border-l-teal-600 bg-teal-50",
            "dark:border-l-teal-400 dark:bg-teal-500/10",
        ].join(" "),

        event: [
            "border-l-slate-500 bg-slate-50",
            "dark:border-l-slate-400 dark:bg-slate-500/10",
        ].join(" "),

        deadline: [
            "border-l-amber-600 bg-amber-50",
            "dark:border-l-amber-400 dark:bg-amber-500/10",
        ].join(" "),
    },

    eventIconTypes: {
        task_deadline: "text-blue-600 dark:text-blue-400",
        meeting: "text-violet-600 dark:text-violet-400",
        appointment: "text-teal-600 dark:text-teal-400",
        event: "text-slate-500 dark:text-slate-400",
        deadline: "text-amber-600 dark:text-amber-400",
    },
};
