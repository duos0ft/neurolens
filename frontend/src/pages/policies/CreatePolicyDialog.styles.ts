export const createPolicyDialogStyles = {
    form: "flex min-w-0 flex-col gap-5",

    field: "flex min-w-0 flex-col gap-2",

    label: "text-sm font-medium text-fg",

    hint: "text-xs leading-5 text-fg-muted",

    textarea: [
        "w-full min-w-0 resize-y rounded-lg",
        "border border-border bg-bg px-3 py-2.5",
        "text-sm leading-relaxed text-fg",
        "placeholder:text-fg-muted",
        "outline-none transition-colors duration-150",
        "hover:border-border-strong",
        "focus-visible:border-border-strong",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    error: [
        "rounded-lg bg-neg-bg px-3 py-2",
        "text-sm text-neg-fg",
    ].join(" "),
};
