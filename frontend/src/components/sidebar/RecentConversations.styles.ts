export const recentConversationsStyles = {
    root: [
        "flex min-h-0 flex-1 flex-col gap-2",
        "px-1",
    ].join(" "),

    toggle: [
        "flex w-full shrink-0 items-center",
        "justify-between gap-2 rounded-lg",
        "px-3 py-2 text-left",
        "transition-colors hover:bg-muted",
        "focus-visible:outline-2 focus-visible:outline-border-strong",
    ].join(" "),

    heading: [
        "text-eyebrow font-semibold uppercase",
        "tracking-eyebrow text-fg-muted",
    ].join(" "),

    toggleRight: [
        "flex shrink-0 items-center gap-2",
    ].join(" "),

    count: [
        "text-caption tabular-nums text-fg-muted",
    ].join(" "),

    chevron: [
        "size-4 text-fg-muted",
        "transition-transform duration-200",
    ].join(" "),

    chevronCollapsed: "rotate-[-90deg]",

    content: [
        "flex min-h-0 flex-1 flex-col",
        "overflow-hidden",
    ].join(" "),

    list: [
        "flex min-h-0 flex-1 flex-col gap-1",
        "overflow-y-auto overscroll-contain",
        "px-1 pb-2",
    ].join(" "),

    item: [
        "group relative flex w-full min-w-0 items-center",
        "gap-1 rounded-lg px-2 py-1.5",
        "transition-colors duration-150",
        "hover:bg-muted/60",
    ].join(" "),

    active: [
        "bg-muted",
    ].join(" "),

    conversationLink: [
        "flex min-w-0 flex-1 flex-col gap-1",
        "rounded-md px-1 py-1.5 text-left",
        "outline-none",
        "focus-visible:outline-2",
        "focus-visible:outline-accent",
        "focus-visible:outline-offset-2",
    ].join(" "),

    title: [
        "block w-full truncate",
        "text-sm font-medium leading-ui text-fg-body",
    ].join(" "),

    activeTitle: [
        "font-semibold text-fg",
    ].join(" "),

    date: [
        "text-caption leading-ui text-fg-muted",
    ].join(" "),

    empty: [
        "px-3 py-3 text-sm text-fg-muted",
    ].join(" "),

    error: [
        "flex flex-col gap-2 px-3 py-3",
        "text-sm text-neg-fg",
    ].join(" "),
};
