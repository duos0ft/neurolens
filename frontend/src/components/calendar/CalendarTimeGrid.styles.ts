export const calendarTimeGridStyles = {
    root: [
        "min-w-0 overflow-hidden rounded-xl",
        "border border-border bg-surface",
    ].join(" "),

    header: [
        "grid border-b border-border bg-surface",
    ].join(" "),

    dayHeading: [
        "flex min-w-0 items-center justify-center gap-1.5",
        "px-2 py-3 text-center",
        "text-xs font-semibold text-fg",
    ].join(" "),

    dayHeadingButton: [
        "flex min-w-0 items-center justify-center gap-2",
        "rounded-md px-2 py-1",
        "transition-colors duration-150",
        "hover:bg-muted",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    dayHeadingToday: [
        "bg-accent-soft text-accent",
        "hover:bg-accent-soft",
    ].join(" "),

    todayNumber: [
        "flex size-7 items-center justify-center",
        "rounded-full bg-accent text-xs font-semibold text-white",
    ].join(" "),

    dayHeadingWeekday: "text-xs font-medium",

    allDay: [
        "grid min-h-11 border-b border-border bg-subtle",
    ].join(" "),

    allDayLabel: [
        "px-1 py-3 text-center",
        "text-xs text-fg-muted",
    ].join(" "),

    allDayColumn: [
        "flex min-w-0 flex-col gap-1.5",
        "border-l border-border p-2",
    ].join(" "),

    allDayToday: "bg-accent-soft/40",

    timelineScroll: [
        "h-[min(65dvh,640px)] overflow-y-auto overflow-x-hidden",
        "[scrollbar-width:thin]",
        "[scrollbar-color:var(--border-strong)_transparent]",
    ].join(" "),

    timeline: "grid min-w-0",

    hours: "relative",

    hour: [
        "absolute right-2",
        "text-xs tabular-nums text-fg-muted",
    ].join(" "),

    dayColumn: [
        "relative min-w-0 border-l border-border",
        "bg-[repeating-linear-gradient(to_bottom,transparent_0px,transparent_63px,var(--border)_63px,var(--border)_64px)]",
    ].join(" "),

    dayColumnToday: [
        "bg-accent-soft/20",
    ].join(" "),

    positionedEvent: [
        "absolute z-10 min-w-0",
    ].join(" "),

    currentTimeLine: [
        "pointer-events-none absolute inset-x-0 z-20",
        "border-t border-accent",
    ].join(" "),

    currentTimeDot: [
        "absolute -left-1 -top-[4.5px]",
        "size-2 rounded-full bg-accent",
    ].join(" "),

    currentTimeLabel: [
        "pointer-events-none absolute right-1 z-20",
        "-translate-y-1/2 rounded-md",
        "bg-accent px-1.5 py-0.5",
        "text-[10px] font-medium tabular-nums text-white",
    ].join(" "),

    event: [
        "flex h-full min-w-0 items-start gap-1.5",
        "overflow-hidden rounded-[4px]",
        "border-l-[3px] px-2 py-1.5",
        "text-fg",
    ].join(" "),

    eventIcon: "size-3.5 shrink-0",

    eventDetails: [
        "flex min-w-0 flex-col gap-0.5",
    ].join(" "),

    eventTitle: [
        "min-w-0 text-xs font-semibold",
        "leading-snug break-words",
    ].join(" "),

    eventTime: [
        "text-xs tabular-nums text-fg-muted",
    ].join(" "),

    eventCompact: [
        "min-h-9 items-start rounded-[4px]",
        "px-2 py-2",
    ].join(" "),

    eventCompactTitle: [
        "line-clamp-2 whitespace-normal",
        "break-words leading-[1.4]",
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

    eventCompleted: [
        "border-l-border-strong! bg-muted/60!",
        "opacity-65",
    ].join(" "),

    eventCompletedIcon: [
        "text-fg-muted!",
    ].join(" "),

    eventCompletedTitle: [
        "text-fg-muted line-through decoration-fg-muted/60",
    ].join(" "),

    allDayMore: [
        "self-start rounded px-2 py-1",
        "text-xs font-medium text-fg-muted",
        "transition-colors duration-150",
        "hover:bg-muted hover:text-fg",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    allDayEmpty: [
        "px-2 py-1 text-xs text-fg-faint",
    ].join(" "),

    eventDeadline: [
        "h-full min-h-0 rounded-[4px]",
        "px-2 py-2",
    ].join(" "),

    eventDeadlineTitle: [
        "line-clamp-2 whitespace-normal",
        "break-words leading-snug",
    ].join(" "),

};
