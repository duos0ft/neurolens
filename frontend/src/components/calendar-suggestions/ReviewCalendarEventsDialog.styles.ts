export const reviewCalendarEventsDialogStyles = {
    form: [
        "grid min-h-0 grid-cols-1 gap-4",
        "max-h-[min(70dvh,640px)] overflow-y-auto",
        "md:grid-cols-[170px_minmax(0,1fr)]",
        "md:gap-0 md:overflow-hidden",
    ].join(" "),

    navigation: [
        "flex min-w-0 gap-2 overflow-x-auto",
        "border-b border-border pb-3",
        "md:flex-col md:overflow-y-auto",
        "md:border-b-0 md:border-r md:pb-0 md:pr-3",
    ].join(" "),

    eventTab: [
        "flex min-h-10 min-w-[140px] items-center gap-2",
        "rounded-lg px-2.5 py-2",
        "text-left text-sm text-fg-body",
        "hover:bg-muted",
        "md:w-full md:min-w-0",
    ].join(" "),

    eventTabActive: [
        "bg-muted font-medium text-fg",
    ].join(" "),

    eventNumber: [
        "flex size-6 shrink-0 items-center justify-center",
        "rounded-md bg-surface",
        "text-xs font-semibold text-fg-muted",
    ].join(" "),

    eventTitle: "min-w-0 flex-1 truncate",

    editor: [
        "flex min-h-0 min-w-0 flex-col gap-4",
        "md:overflow-y-auto md:pl-5 md:pr-2",
    ].join(" "),

    indicator: [
        "text-eyebrow font-semibold uppercase",
        "tracking-eyebrow text-fg-muted",
    ].join(" "),

    field: "flex min-w-0 flex-col gap-1.5",

    label: "text-sm font-medium text-fg",

    hint: "text-xs leading-5 text-fg-muted",

    textarea: [
        "w-full min-w-0 resize-y rounded-lg",
        "border border-border bg-bg px-3 py-2.5",
        "text-sm leading-relaxed text-fg",
        "outline-none transition-colors",
        "hover:border-border-strong",
        "focus-visible:border-border-strong",
    ].join(" "),

    fieldGrid: [
        "grid grid-cols-1 gap-x-4 gap-y-4",
        "sm:grid-cols-2",
    ].join(" "),

    checkboxField: [
        "flex min-h-10 items-center",
    ].join(" "),

    timeInput: [
        "h-10 w-full min-w-0 rounded-lg",
        "border border-border bg-bg px-3",
        "text-sm text-fg",
        "outline-none",
        "focus-visible:border-border-strong",
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
};
