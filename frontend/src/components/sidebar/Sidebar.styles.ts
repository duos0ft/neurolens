export const sidebarStyles = {
    root: "flex h-dvh shrink-0 flex-col border-r border-border bg-bg",

    header: "flex h-16 shrink-0 items-center gap-3 px-5",
    logo: "size-9 shrink-0 rounded-full",
    brand: "text-xl font-semibold tracking-tight text-fg",
    content: "flex min-h-0 flex-1 flex-col overflow-y-auto px-3 py-4",

    nav: "flex flex-col gap-1",
    navLink:
        "flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-muted-fg transition-colors hover:bg-muted hover:text-fg",
    navLinkActive: "bg-muted text-fg",
    navIcon: "size-5 shrink-0",

    section: "mt-8",
    sectionLabel: "px-3 pb-3 text-xs font-semibold uppercase tracking-wider text-muted-fg",

    coworkers: "flex flex-col gap-1",
    coworker: "flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-muted",
    coworkerActive: "bg-muted",
    avatar: "flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-fg",
    coworkerInfo: "flex min-w-0 flex-1 flex-col",
    coworkerName: "truncate text-sm font-medium text-fg",
    coworkerRole: "truncate text-xs text-muted-fg",

    adminToggle: "h-auto w-full justify-between rounded-xl px-3 py-2.5 text-sm font-medium text-fg hover:bg-muted",
    adminToggleContent: "flex items-center gap-3",
    adminSubnav: "mt-1 ml-5 flex flex-col gap-1 border-l border-border pl-3",
    adminChevron: "size-4 transition-transform duration-200",
    adminChevronOpen: "rotate-180",
    adminSubnavLink: "rounded-lg px-3 py-2 text-sm text-muted-fg transition-colors hover:bg-muted hover:text-fg",
    adminSubnavLinkActive: "bg-muted font-medium text-fg",

    footer: "shrink-0 border-t border-border p-4",
    account: "flex w-full items-center gap-3 rounded-xl p-3 text-left transition-colors hover:bg-muted",
    accountInfo: "flex min-w-0 flex-1 flex-col",
    accountName: "truncate text-sm font-medium text-fg",
    accountRole: "truncate text-xs text-muted-fg",
};
