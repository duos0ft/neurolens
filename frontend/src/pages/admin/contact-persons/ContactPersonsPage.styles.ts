export const contactPersonsPageStyles = {
    root: "flex w-full flex-col gap-7",

    directory: "flex flex-col gap-4",

    toolbar: "flex flex-wrap items-center gap-3",

    name: "font-medium text-fg",

    email: "block truncate text-sm text-fg-muted",

    responsibility: "text-sm text-fg-body",

    secondary: "text-sm text-fg-muted",

    status: "inline-flex rounded-md px-2.5 py-1 text-xs font-medium",

    primaryBadge: [
        "inline-flex rounded-md px-2.5 py-1 text-xs font-medium",
        "bg-blue-500/10 text-blue-700 dark:text-blue-400",
    ].join(" "),

    activeBadge: [
        "inline-flex rounded-md px-2.5 py-1 text-xs font-medium",
        "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
    ].join(" "),

    inactiveBadge: [
        "inline-flex rounded-md bg-muted px-2.5 py-1",
        "text-xs font-medium text-fg-muted",
    ].join(" "),

    error: [
        "rounded-lg border border-border bg-surface",
        "px-5 py-12 text-center text-sm text-neg-fg",
    ].join(" "),

    actionIcon: "size-4",
};
