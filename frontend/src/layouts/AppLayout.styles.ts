export const appLayoutStyles = {
    root: "flex min-h-dvh bg-bg text-fg",
    content: "flex min-w-0 flex-1 flex-col",

    header: [
        "flex h-16 shrink-0 items-center gap-3",
        "border-b border-border bg-bg px-5",
        "lg:px-8",
    ].join(" "),

    main: "min-w-0 flex-1",
    mainInner: "w-full px-5 py-8 lg:px-16 lg:py-10",

    backdrop: "fixed inset-0 z-40 bg-black/40 lg:hidden",
    mobileHeader: "flex items-center px-4 py-3 lg:hidden",
    mobileToggle: "flex size-9 items-center justify-center rounded-lg transition-colors hover:bg-slate-100",
    toggleIcon: "size-5",
};
