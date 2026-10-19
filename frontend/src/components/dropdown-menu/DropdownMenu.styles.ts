export const dropdownMenuStyles = {
    trigger: [
        "inline-flex size-9 items-center justify-center",
        "rounded-md text-fg-muted transition-colors",
        "hover:bg-muted hover:text-fg",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    menu: [
        "m-0 w-48 overflow-hidden rounded-md border border-border",
        "bg-surface p-1 text-fg shadow-lg",
    ].join(" "),

    item: [
        "flex w-full items-center gap-2 rounded-sm px-3 py-2",
        "text-left text-sm text-fg outline-none transition-colors",
        "hover:bg-muted focus-visible:bg-muted",
        "disabled:cursor-not-allowed disabled:opacity-40",
    ].join(" "),

    destructive: [
        "text-red-600 dark:text-red-400",
        "hover:bg-red-500/10 focus-visible:bg-red-500/10",
    ].join(" "),
};
