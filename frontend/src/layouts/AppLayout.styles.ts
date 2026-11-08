export const appLayoutStyles = {
    root: [
        "flex h-dvh min-h-0 overflow-hidden",
        "bg-bg text-fg",
    ].join(" "),

    content: [
        "flex min-h-0 min-w-0 flex-1 flex-col",
    ].join(" "),

    main: [
        "flex min-h-0 min-w-0 flex-1 flex-col",
        "overflow-y-auto",
    ].join(" "),

    mainInner: [
        "w-full flex-1",
        "px-5 py-8 lg:px-10 lg:py-8",
    ].join(" "),

    // Used for workspace-style pages such as Assistant.
    // The following step will apply this to the chat route.
    workspaceMain: [
        "flex min-h-0 min-w-0 flex-1 flex-col",
        "overflow-hidden",
    ].join(" "),

    workspaceMainInner: [
        "flex min-h-0 min-w-0 flex-1 flex-col",
        "overflow-hidden",
    ].join(" "),

    backdrop: [
        "fixed inset-0 z-40 bg-black/40",
        "lg:hidden",
    ].join(" "),

    mobileHeader: [
        "flex shrink-0 items-center",
        "border-b border-border bg-bg",
        "px-4 py-3 lg:hidden",
    ].join(" "),

    mobileToggle: [
        "flex size-10 items-center justify-center",
        "rounded-lg text-fg-body",
        "transition-colors hover:bg-muted",
        "focus-visible:outline-2 focus-visible:outline-accent",
    ].join(" "),

    toggleIcon: "size-5",
};
