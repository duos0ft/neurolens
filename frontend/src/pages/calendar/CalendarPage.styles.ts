export const calendarPageStyles = {
    root: "mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8",

    calendar: [
        "neurolens-calendar flex flex-col overflow-hidden",
        "rounded-xl border border-border bg-surface",
    ].join(" "),

    toolbar: [
        "flex flex-wrap items-center justify-between gap-4",
        "border-b border-border px-4 py-3",
    ].join(" "),

    navigation: "flex items-center gap-2",

    periodTitle: "ml-2 text-base font-semibold text-fg",

    toolbarActions: "flex flex-wrap items-center gap-3",

    viewSwitch: [
        "flex items-center gap-1 rounded-lg",
        "border border-border bg-subtle p-1",
    ].join(" "),

    calendarBody: "min-w-0 p-3",

    loading: "px-4 py-2 text-xs text-fg-muted",

    error: [
        "flex flex-wrap items-center justify-between gap-3",
        "border-b border-border px-4 py-3",
        "text-sm text-neg-fg",
    ].join(" "),

    eventContent: [
        "flex min-w-0 items-start gap-1.5",
        "px-1 py-0.5",
        "whitespace-normal",
    ].join(" "),

    eventIcon: "mt-0.5 size-3.5 shrink-0",

    eventTitle: [
        "min-w-0 flex-1",
        "whitespace-normal break-words",
        "text-xs font-medium leading-4",
    ].join(" "),

    eventCompleted: "opacity-60 line-through",

    legend: "flex flex-wrap items-center gap-5",

    legendItem: [
        "flex items-center gap-2 text-xs text-fg-muted",
        "[&_svg]:size-4",
    ].join(" "),
};
