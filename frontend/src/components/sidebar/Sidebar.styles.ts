export const sidebarStyles = {
    root: [
        "flex h-dvh min-h-0 shrink-0 flex-col",
        "border-r border-border bg-bg",
    ].join(" "),

    header: [
        "flex h-16 shrink-0 items-center gap-3",
        "px-5",
    ].join(" "),

    logo: [
        "size-9 shrink-0 rounded-full",
        "bg-orb",
    ].join(" "),

    brand: [
        "text-lg font-semibold tracking-tight",
        "text-fg",
    ].join(" "),

    content: [
        "flex min-h-0 flex-1 flex-col",
        "overflow-y-auto px-3 py-4",
    ].join(" "),

    nav: [
        "flex shrink-0 flex-col gap-1",
    ].join(" "),

    navLink: [
        "flex w-full items-center gap-3",
        "rounded-lg px-3 py-2.5",
        "text-sm font-medium text-fg-body",
        "transition-colors",
        "hover:bg-muted hover:text-fg",
        "focus-visible:outline-2 focus-visible:outline-border-strong",
    ].join(" "),

    navLinkActive: [
        "bg-muted text-fg",
    ].join(" "),

    navIcon: "size-5 shrink-0",

    recentSection: [
        "mt-6 flex min-h-0 flex-1 flex-col",
        "overflow-hidden",
    ].join(" "),

    section: [
        "mt-auto shrink-0 pt-5",
    ].join(" "),

    sectionLabel: [
        "px-3 pb-3 text-xs font-semibold",
        "uppercase tracking-wider text-fg-muted",
    ].join(" "),

    coworkers: "flex flex-col gap-1",

    coworker: [
        "flex items-center gap-3",
        "rounded-lg px-3 py-2.5",
        "transition-colors hover:bg-muted",
    ].join(" "),

    coworkerActive: "bg-muted",

    avatar: [
        "flex size-9 shrink-0 items-center justify-center",
        "rounded-full bg-muted",
        "text-xs font-semibold text-fg-muted",
    ].join(" "),

    coworkerInfo: "flex min-w-0 flex-1 flex-col",

    coworkerName: "truncate text-sm font-medium text-fg",

    coworkerRole: "truncate text-xs text-fg-muted",

    adminToggle: [
        "h-auto w-full justify-between",
        "rounded-lg px-3 py-2.5",
        "text-sm font-medium text-fg-body",
        "hover:bg-muted hover:text-fg",
    ].join(" "),

    adminToggleContent: "flex items-center gap-3",

    adminSubnav: [
        "mt-1 ml-5 flex flex-col gap-1",
        "border-l border-border pl-3",
    ].join(" "),

    adminChevron: [
        "size-4 transition-transform duration-200",
    ].join(" "),

    adminChevronOpen: "rotate-180",

    adminSubnavLink: [
        "rounded-lg px-3 py-2 text-sm",
        "text-fg-muted transition-colors",
        "hover:bg-muted hover:text-fg",
    ].join(" "),

    adminSubnavLinkActive: [
        "bg-muted font-medium text-fg",
    ].join(" "),

    footer: [
        "shrink-0 border-t border-border p-3",
    ].join(" "),

    account: [
        "flex w-full items-center gap-3",
        "rounded-lg p-3 text-left",
        "transition-colors hover:bg-muted",
    ].join(" "),

    accountInfo: "flex min-w-0 flex-1 flex-col",

    accountName: "truncate text-sm font-medium text-fg",

    accountRole: "truncate text-xs text-fg-muted",
};
