export const employeesPageStyles = {
    root: "flex w-full flex-col gap-7",
    pageHeader: "flex flex-wrap items-center justify-between gap-4",
    title: "text-2xl font-semibold tracking-tight text-fg",
    description: "mt-1 text-sm text-fg-muted",

    directory: "flex flex-col gap-4",
    toolbar: "flex flex-wrap items-center gap-3",

    employeeCell: "flex min-w-0 items-center gap-3 whitespace-nowrap",
    employeeName: "font-medium text-fg",
    employeeEmail: "block truncate text-sm text-fg-muted",

    role: "capitalize text-fg-body",
    status: "inline-flex rounded-md px-2.5 py-1 text-xs font-medium",
    date: "text-sm text-fg-muted",

    error: "rounded-lg border border-border bg-surface px-5 py-12 text-center text-sm text-neg-fg",
};
