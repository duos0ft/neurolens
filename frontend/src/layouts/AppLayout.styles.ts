export const appLayoutStyles = {
    root: "flex min-h-dvh bg-bg text-fg",
    content: "flex min-w-0 flex-1 flex-col",

    header: [
        "flex h-16 shrink-0 items-center gap-3",
        "border-b border-border bg-bg px-5",
        "lg:px-8",
    ].join(" "),

    mobileToggle: [
        "inline-flex size-9 shrink-0 items-center justify-center",
        "rounded-lg text-fg transition-colors hover:bg-muted",
        "lg:hidden",
    ].join(" "),

    toggleIcon: "size-5",

    breadcrumbs: "flex min-w-0 items-center gap-3 text-sm",
    breadcrumbParent: "text-fg-muted",
    breadcrumbLink: "text-fg-muted transition-colors hover:text-fg",
    breadcrumbSeparator: "text-fg-muted",
    breadcrumbCurrent: "truncate font-medium text-fg",

    main: "min-w-0 flex-1",
    mainInner: "w-full px-5 py-8 lg:px-16 lg:py-10",

    backdrop: "fixed inset-0 z-40 bg-black/40 lg:hidden",
};
