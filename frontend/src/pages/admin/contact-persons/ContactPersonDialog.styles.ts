export const contactPersonDialogStyles = {
    form: "flex flex-col gap-5",

    field: "flex min-w-0 flex-col gap-2",

    grid: "grid grid-cols-1 gap-4 sm:grid-cols-2",

    label: "text-sm font-medium text-fg",

    hint: "text-xs leading-5 text-fg-muted",

    primaryOption: [
        "flex cursor-pointer items-start gap-3",
        "rounded-lg border border-border bg-surface",
        "p-4",
    ].join(" "),

    checkbox: [
        "mt-0.5 size-4 shrink-0 cursor-pointer",
        "accent-current",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    primaryText: "flex flex-col gap-1",

    primaryTitle: "text-sm font-medium text-fg",
};
