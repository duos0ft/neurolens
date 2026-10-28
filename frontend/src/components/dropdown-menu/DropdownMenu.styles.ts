export const dropdownMenuStyles = {
    trigger: [
        "inline-flex size-8 shrink-0 items-center justify-center",
        "rounded-lg text-fg-muted transition-colors",
        "hover:bg-muted hover:text-fg",
        "data-[open=true]:bg-muted data-[open=true]:text-fg",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    menu: [
        "m-0 overflow-hidden rounded-lg border border-border",
        "bg-surface p-1 text-fg shadow-lg",
    ].join(" "),

    item: [
        "flex min-h-9 w-full items-center gap-2.5",
        "rounded-md px-2.5 py-2 text-left",
        "text-sm font-medium text-fg",
        "outline-none transition-colors",
        "hover:bg-muted focus-visible:bg-muted",
        "disabled:cursor-not-allowed disabled:opacity-40",
    ].join(" "),

    itemIcon: [
        "flex size-4 shrink-0 items-center justify-center",
        "text-fg-muted [&_svg]:size-4",
    ].join(" "),

    destructive: [
        "text-neg-fg",
        "hover:bg-neg-fg/10 focus-visible:bg-neg-fg/10",
    ].join(" "),

    destructiveIcon: "text-neg-fg",
};
