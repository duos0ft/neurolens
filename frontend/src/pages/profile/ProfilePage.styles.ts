export const profilePageStyles = {
    root: "mx-auto flex w-full max-w-5xl flex-col gap-6",

    header: "flex flex-col gap-1",
    title: "text-2xl font-semibold tracking-tight text-fg",
    description: "text-sm text-fg-body",

    profileCard: "flex w-full flex-col gap-6",
    profileHeader: "flex items-center gap-4",
    profileInfo: "flex min-w-0 flex-col gap-1",
    profileName: "truncate text-lg font-semibold text-fg",
    profileSubtitle: "text-sm text-fg-muted",

    sectionHeader: "flex flex-col gap-1",
    sectionTitle: "text-base font-semibold text-fg",
    sectionDescription: "text-sm text-fg-body",

    form: "flex flex-col gap-6",
    fields: "grid grid-cols-1 gap-5 sm:grid-cols-2",
    field: "flex min-w-0 flex-col gap-2",
    label: "text-sm font-medium text-fg",
    hint: "text-xs text-fg-muted",

    divider: "h-px bg-border",
    actions: "flex justify-end",

    error: "text-xs text-neg-fg",
};
