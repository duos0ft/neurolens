export const sidebarAccountStyles = {
    root: "relative shrink-0 border-t border-border p-3",

    trigger: "h-auto w-full justify-start gap-3 rounded-xl px-2.5 py-2.5 text-left hover:bg-muted",

    info: "flex min-w-0 flex-1 flex-col items-start gap-0.5",
    name: "w-full truncate text-sm font-medium text-fg",
    subtitle: "w-full truncate text-xs text-muted-fg",
    chevron: "size-4 shrink-0 text-muted-fg",

    menu: "absolute right-3 bottom-[calc(100%+0.5rem)] left-3 z-50 rounded-xl border border-border bg-bg p-1.5 shadow-lg",

    menuItem:
        "h-auto w-full justify-start gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-normal text-fg hover:bg-muted focus-visible:bg-muted",

    menuIcon: "size-4 shrink-0 text-muted-fg",
    separator: "my-1.5 h-px bg-border",
};
