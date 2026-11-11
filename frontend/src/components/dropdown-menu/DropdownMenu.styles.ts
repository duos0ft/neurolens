export const dropdownMenuStyles = {
    trigger: [
        "inline-flex size-8 shrink-0 items-center justify-center",
        "rounded-lg text-fg-muted",
        "transition-colors duration-150",
        "hover:bg-muted hover:text-fg",
        "data-[open=true]:bg-muted data-[open=true]:text-fg",
        "focus-visible:outline-2 focus-visible:outline-border-strong",
        "disabled:cursor-not-allowed disabled:opacity-40",
    ].join(" "),

    triggerIcon: "size-[18px]",

    menu: [
        "rounded-xl border border-border",
        "bg-surface p-1.5 text-fg",
        "shadow-popover",
        "outline-none",
    ].join(" "),

    item: [
        "flex min-h-9 w-full items-center gap-2.5",
        "rounded-lg px-2.5 py-2 text-left",
        "text-sm font-medium leading-ui text-fg-body",
        "outline-none transition-colors duration-150",
        "hover:bg-muted hover:text-fg",
        "focus-visible:bg-muted focus-visible:text-fg",
        "disabled:cursor-not-allowed disabled:opacity-40",
    ].join(" "),

    itemIcon: [
        "flex size-4 shrink-0 items-center justify-center",
        "text-fg-muted [&_svg]:size-4",
    ].join(" "),

    itemLabel: "min-w-0 flex-1 whitespace-nowrap",

    destructive: [
        "text-destructive",
        "hover:bg-destructive/10 hover:text-destructive",
        "focus-visible:bg-destructive/10 focus-visible:text-destructive",
    ].join(" "),

    destructiveIcon: "text-destructive",

    separator: "my-1.5 border-t border-border",
};
