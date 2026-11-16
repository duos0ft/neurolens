export const uploadPolicyVersionDialogStyles = {
    form: "flex min-w-0 flex-col gap-5",

    field: "flex min-w-0 flex-col gap-2",

    label: "text-sm font-medium text-fg",

    hint: "text-xs leading-5 text-fg-muted",

    fileInput: [
        "block w-full min-w-0 rounded-lg border border-border bg-bg",
        "px-3 py-2.5 text-sm text-fg",
        "file:mr-3 file:rounded-md file:border-0",
        "file:bg-surface file:px-3 file:py-1.5",
        "file:text-sm file:font-medium file:text-fg",
        "hover:file:cursor-pointer",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    fileDetails: "text-xs text-fg-muted",

    error: [
        "rounded-lg bg-neg-bg px-3 py-2",
        "text-sm text-neg-fg",
    ].join(" "),
};
