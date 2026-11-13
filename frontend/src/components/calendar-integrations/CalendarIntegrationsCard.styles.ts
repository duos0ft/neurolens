export const calendarIntegrationsStyles = {
    card: "flex w-full flex-col gap-5",

    header: "flex flex-col gap-1",
    title: "text-base font-semibold text-fg",
    description: "text-sm text-fg-body",

    divider: "h-px bg-border",

    provider: [
        "flex flex-col gap-4",
        "sm:flex-row sm:items-center sm:justify-between",
    ].join(" "),

    providerInfo: "flex min-w-0 items-center gap-3",

    googleIcon: [
        "flex size-11 shrink-0 items-center justify-center",
        "rounded-xl border border-border bg-bg text-fg",
    ].join(" "),

    microsoftIcon: [
        "flex size-11 shrink-0 items-center justify-center",
        "rounded-xl border border-border bg-bg text-fg-muted",
    ].join(" "),

    icon: "size-5",

    providerDetails: "flex min-w-0 flex-col gap-1",

    providerName: "text-sm font-semibold text-fg",

    providerDescription: [
        "break-all text-xs text-fg-muted",
    ].join(" "),

    connected: "text-xs font-medium text-emerald-600",

    providerActions: "flex shrink-0 items-center gap-2",

    comingSoon: "text-xs text-fg-muted",

    errorRow: [
        "flex flex-wrap items-center justify-between gap-3",
    ].join(" "),

    error: "text-xs text-neg-fg",

    confirmation: [
        "flex flex-col gap-4",
        "rounded-lg border border-border bg-bg p-4",
    ].join(" "),

    confirmationContent: "flex flex-col gap-2",

    confirmationTitle: "text-sm font-semibold text-fg",

    confirmationDescription: "text-sm leading-relaxed text-fg-body",

    confirmationActions: [
        "flex flex-wrap justify-end gap-2",
    ].join(" "),
};
